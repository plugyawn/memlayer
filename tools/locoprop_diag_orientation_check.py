#!/usr/bin/env python3
"""Reference checks for diagonal feature-Gram storage conventions.

The current speedrun model stores some affine weights as (out, in) and some as
(in, out).  A diagonal feature Gram must therefore scale different axes.  The
same axis mapping is used whether the preconditioned gradient feeds NorMuon or a
direct LocoProp-S update.
"""

from __future__ import annotations

import argparse

import numpy as np

try:
    import torch
except ModuleNotFoundError:
    torch = None


def out_in_reference(x: torch.Tensor, grad_y: torch.Tensor, weight: torch.Tensor, ridge: float) -> tuple[torch.Tensor, torch.Tensor]:
    """Y = X @ W.T, W is (out, in), dW = dY.T @ X; scale columns."""
    del weight
    grad_w = grad_y.T @ x
    gram = x.T @ x
    full_delta = -(grad_w @ torch.linalg.inv(gram + ridge * torch.eye(gram.shape[0], device=x.device, dtype=x.dtype)))
    diag_delta = -(grad_w / (gram.diag().clamp_min(0) + ridge).view(1, -1))
    return full_delta, diag_delta


def in_out_reference(x: torch.Tensor, grad_y: torch.Tensor, weight: torch.Tensor, ridge: float) -> tuple[torch.Tensor, torch.Tensor]:
    """Y = X @ W, W is (in, out), dW = X.T @ dY; scale rows."""
    del weight
    grad_w = x.T @ grad_y
    gram = x.T @ x
    full_delta = -(torch.linalg.inv(gram + ridge * torch.eye(gram.shape[0], device=x.device, dtype=x.dtype)) @ grad_w)
    diag_delta = -(grad_w / (gram.diag().clamp_min(0) + ridge).view(-1, 1))
    return full_delta, diag_delta


def check_diagonal_equivalence(device: str) -> None:
    assert torch is not None
    torch.manual_seed(1234)
    dtype = torch.float64
    batch = 17
    in_dim = 5
    out_dim = 7
    ridge = 1e-3

    x = torch.randn(batch, in_dim, dtype=dtype, device=device)
    grad_y = torch.randn(batch, out_dim, dtype=dtype, device=device)
    w_out_in = torch.randn(out_dim, in_dim, dtype=dtype, device=device)
    w_in_out = torch.randn(in_dim, out_dim, dtype=dtype, device=device)

    gram_diag = torch.diag(torch.diag(x.T @ x))
    out_in_full_diag = -(grad_y.T @ x) @ torch.linalg.inv(
        gram_diag + ridge * torch.eye(in_dim, dtype=dtype, device=device)
    )
    in_out_full_diag = -torch.linalg.inv(
        gram_diag + ridge * torch.eye(in_dim, dtype=dtype, device=device)
    ) @ (x.T @ grad_y)

    _, out_in_diag = out_in_reference(x, grad_y, w_out_in, ridge)
    _, in_out_diag = in_out_reference(x, grad_y, w_in_out, ridge)

    torch.testing.assert_close(out_in_diag, out_in_full_diag)
    torch.testing.assert_close(in_out_diag, in_out_full_diag)


def check_mlp_bank_axes(device: str) -> None:
    assert torch is not None
    torch.manual_seed(5678)
    dtype = torch.float64
    tokens = 19
    dim = 6
    hidden = 11
    ridge = 1e-2

    x = torch.randn(tokens, dim, dtype=dtype, device=device)
    w1 = torch.randn(hidden, dim, dtype=dtype, device=device)
    pre = x @ w1.T
    post = torch.relu(pre).square()
    grad_hidden = torch.randn(tokens, hidden, dtype=dtype, device=device)
    grad_out = torch.randn(tokens, dim, dtype=dtype, device=device)

    fc_grad = grad_hidden.T @ x
    fc_diag = x.square().sum(dim=0)
    fc_delta = -(fc_grad / (fc_diag + ridge).view(1, -1))
    fc_expected = -(fc_grad @ torch.diag(1.0 / (fc_diag + ridge)))

    proj_grad = post.T @ grad_out
    proj_diag = post.square().sum(dim=0)
    proj_delta = -(proj_grad / (proj_diag + ridge).view(-1, 1))
    proj_expected = -(torch.diag(1.0 / (proj_diag + ridge)) @ proj_grad)

    torch.testing.assert_close(fc_delta, fc_expected)
    torch.testing.assert_close(proj_delta, proj_expected)


def check_grad_scale_consistency(device: str) -> None:
    assert torch is not None
    torch.manual_seed(9012)
    dtype = torch.float64
    grad_scale = 0.125

    grad = torch.randn(7, 5, dtype=dtype, device=device)
    diag = torch.rand(5, dtype=dtype, device=device).add(0.25)
    unscaled = grad / diag.view(1, -1)
    matched = (grad * grad_scale) / (diag * grad_scale).view(1, -1)
    unmatched = (grad * grad_scale) / diag.view(1, -1)

    torch.testing.assert_close(matched, unscaled)
    torch.testing.assert_close(unmatched, unscaled * grad_scale)


def print_current_mapping() -> None:
    rows = [
        ("qk_bank", "F.linear(attn_in, qk)", "out x in", "columns", "attn input, dim 768"),
        ("vo_bank V rows", "F.linear(attn_in, v)", "out x in", "columns", "attn input, dim 768"),
        ("vo_bank O rows", "F.linear(attn_out, o)", "out x in", "columns", "attention output, dim 768"),
        ("mlp_bank c_fc", "linear_relu_square(x, W1)", "out x in", "columns", "MLP input, dim 768"),
        ("mlp_bank c_proj", "post @ W2", "in x out", "rows", "MLP post-activation, dim 3072"),
    ]
    width = max(len(row[0]) for row in rows)
    for name, forward, storage, axis, feature in rows:
        print(f"{name:<{width}}  storage={storage:<8} scale_axis={axis:<7} feature={feature}  forward={forward}")


def check_numpy_fallback() -> None:
    rng = np.random.default_rng(1234)
    batch = 17
    in_dim = 5
    out_dim = 7
    ridge = 1e-3

    x = rng.standard_normal((batch, in_dim))
    grad_y = rng.standard_normal((batch, out_dim))
    gram_diag = np.diag(np.diag(x.T @ x))

    grad_out_in = grad_y.T @ x
    out_in_diag = -(grad_out_in / (np.diag(gram_diag) + ridge)[None, :])
    out_in_expected = -(grad_out_in @ np.linalg.inv(gram_diag + ridge * np.eye(in_dim)))
    np.testing.assert_allclose(out_in_diag, out_in_expected)

    grad_in_out = x.T @ grad_y
    in_out_diag = -(grad_in_out / (np.diag(gram_diag) + ridge)[:, None])
    in_out_expected = -(np.linalg.inv(gram_diag + ridge * np.eye(in_dim)) @ grad_in_out)
    np.testing.assert_allclose(in_out_diag, in_out_expected)

    tokens = 19
    dim = 6
    hidden = 11
    ridge = 1e-2
    x = rng.standard_normal((tokens, dim))
    w1 = rng.standard_normal((hidden, dim))
    pre = x @ w1.T
    post = np.maximum(pre, 0) ** 2
    grad_hidden = rng.standard_normal((tokens, hidden))
    grad_out = rng.standard_normal((tokens, dim))

    fc_grad = grad_hidden.T @ x
    fc_diag = np.square(x).sum(axis=0)
    np.testing.assert_allclose(
        -(fc_grad / (fc_diag + ridge)[None, :]),
        -(fc_grad @ np.diag(1.0 / (fc_diag + ridge))),
    )

    proj_grad = post.T @ grad_out
    proj_diag = np.square(post).sum(axis=0)
    np.testing.assert_allclose(
        -(proj_grad / (proj_diag + ridge)[:, None]),
        -(np.diag(1.0 / (proj_diag + ridge)) @ proj_grad),
    )

    grad_scale = 0.125
    grad = rng.standard_normal((7, 5))
    diag = rng.random(5) + 0.25
    unscaled = grad / diag[None, :]
    matched = (grad * grad_scale) / (diag * grad_scale)[None, :]
    unmatched = (grad * grad_scale) / diag[None, :]
    np.testing.assert_allclose(matched, unscaled)
    np.testing.assert_allclose(unmatched, unscaled * grad_scale)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    if torch is None:
        if args.device != "cpu":
            raise SystemExit("torch is not installed; only the NumPy CPU fallback is available")
        check_numpy_fallback()
        print_current_mapping()
        print("ok (numpy fallback; torch not installed)")
        return

    check_diagonal_equivalence(args.device)
    check_mlp_bank_axes(args.device)
    check_grad_scale_consistency(args.device)
    print_current_mapping()
    print("ok")


if __name__ == "__main__":
    main()
