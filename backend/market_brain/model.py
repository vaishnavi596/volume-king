"""Small transparent logistic model (ridge, Newton steps). Direction only; the output is
an evidence ratio, never a win probability claim."""
import numpy as np


class Logistic:
    def __init__(self, l2=5.0, iters=25):
        self.l2, self.iters = l2, iters
        self.w = None
        self.mu = None
        self.sd = None

    def fit(self, X, y):
        X = np.asarray(X, float)
        y = np.asarray(y, float)
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0) + 1e-9
        Z = np.hstack([np.ones((len(X), 1)), (X - self.mu) / self.sd])
        w = np.zeros(Z.shape[1])
        reg = np.eye(Z.shape[1]) * self.l2
        reg[0, 0] = 0.0
        for _ in range(self.iters):
            p = 1 / (1 + np.exp(-np.clip(Z @ w, -30, 30)))
            grad = Z.T @ (p - y) + reg @ w
            H = Z.T @ (Z * (p * (1 - p))[:, None]) + reg + np.eye(Z.shape[1]) * 1e-6
            step = np.linalg.solve(H, grad)
            w -= step
            if np.max(np.abs(step)) < 1e-7:
                break
        self.w = w
        return self

    def predict_proba(self, X):
        X = np.asarray(X, float)
        Z = np.hstack([np.ones((len(X), 1)), (X - self.mu) / self.sd])
        return 1 / (1 + np.exp(-np.clip(Z @ self.w, -30, 30)))
