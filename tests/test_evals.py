from evals.run_evals import run_evals

def test_eval_runner():
    res = run_evals()
    assert res["passed"] == res["total"]
