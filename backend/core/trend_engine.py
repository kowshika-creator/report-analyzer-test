from typing import List, Dict, Any, Tuple

BAD_PARAMS = [
    "fasting", "fasting glucose", "hba1c", "total cholesterol", "ldl",
    "triglycerides", "alt", "ast", "creatinine", "tsh", "c-reactive protein", "crp"
]

def compare_longitudinal_trends(
    baseline_date: str,
    current_date: str,
    baseline_metrics: List[Dict[str, Any]],
    current_metrics: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], str]:
    """
    Local Longitudinal Trend Engine:
    Computes absolute deltas, percentage changes, and directional tracking
    (improved, worsened, stable) between baseline and current medical lab reports.
    """
    base_map = {m["biomarker_name"].lower(): m for m in baseline_metrics}
    deltas = []

    for curr in current_metrics:
        b_name = curr["biomarker_name"]
        b_lower = b_name.lower()
        if b_lower in base_map:
            base = base_map[b_lower]
            v_base = base["value"]
            v_curr = curr["value"]
            diff = round(v_curr - v_base, 2)
            pct = round((diff / v_base) * 100, 1) if v_base != 0 else 0.0

            is_bad_param = any(bad in b_lower for bad in BAD_PARAMS)

            if abs(diff) < 0.05:
                direction = "stable"
                insight = f"Your {b_name} remained stable at {v_curr} {curr['unit']} compared to your {baseline_date} baseline."
            elif (diff < 0 and is_bad_param) or (diff > 0 and not is_bad_param):
                direction = "improved"
                action_word = "dropped" if diff < 0 else "increased"
                insight = f"Great progress! Your {b_name} {action_word} by {abs(diff)} {curr['unit']} ({v_base} -> {v_curr} {curr['unit']}) compared to {baseline_date}."
            else:
                direction = "worsened"
                action_word = "rose" if diff > 0 else "dipped"
                insight = f"Attention: Your {b_name} {action_word} by {abs(diff)} {curr['unit']} ({v_base} -> {v_curr} {curr['unit']}) compared to {baseline_date}."

            deltas.append({
                "biomarker_name": b_name,
                "baseline_value": v_base,
                "current_value": v_curr,
                "delta_value": diff,
                "percentage_change": pct,
                "unit": curr["unit"],
                "direction": direction,
                "insight_text": insight
            })

    improved_count = sum(1 for d in deltas if d["direction"] == "improved")
    worsened_count = sum(1 for d in deltas if d["direction"] == "worsened")
    summary = f"Longitudinal trend summary ({baseline_date} -> {current_date}): {improved_count} parameters improved, {worsened_count} parameters require ongoing monitoring."

    return deltas, summary
