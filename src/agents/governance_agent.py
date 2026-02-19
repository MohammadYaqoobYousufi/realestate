def governance_check(prediction, market_median, prd_current):

    flags = []

    if prediction > market_median * 3:
        flags.append("Extreme deviation from local median")

    if prd_current > 1.10:
        flags.append("Regressivity bias detected")

    return {
        "status": "FLAG" if flags else "PASS",
        "issues": flags
    }