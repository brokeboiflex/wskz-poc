"""Same uncoupled AdamW update, releasing each finished gradient immediately."""


def step_and_release(optimizer):
    groups = optimizer.param_groups
    try:
        for group in groups:
            for parameter in group["params"]:
                if parameter.grad is None:
                    continue
                optimizer.param_groups = [{**group, "params": [parameter]}]
                optimizer.step()
                parameter.grad = None
    finally:
        optimizer.param_groups = groups
