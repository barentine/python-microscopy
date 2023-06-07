

def test_gmm_big_grid_search():
    import numpy as np
    n = 13
    X = np.vstack([np.random.randn(10 * (ind + 1), 2) + 10 * ind for ind in range(n)])
    points = {'x': X[:,0], 'y':X[:, 1], 'z': np.zeros(X.shape[0])}
    # plt.scatter(X[:,0], X[:, 1])
    from PYME.recipes.pointcloud import GaussianMixtureModel
    gmm = GaussianMixtureModel(
        mode='gridsearch_bic', n=6 * n,
        n_initializations=2
        )
    ret = gmm.apply_simple(points)
    assert len(np.unique(ret['gmm_label'])) == n
    # plt.scatter(ret['x'], ret['y'], c=ret['gmm_label'])
