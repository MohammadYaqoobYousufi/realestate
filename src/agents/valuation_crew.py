from app.services.inference_service import predict_value
from app.agents.explanation_agent import generate_explanation
from app.agents.governance_agent import governance_check
from app.rag.retriever import retrieve_rules

def run_valuation_pipeline(roll_number):

    inference = predict_value(roll_number)

    rules = retrieve_rules("calgary assessment standards")

    explanation = generate_explanation(
        inference["prediction"],
        shap_values="top_5_placeholder",
        retrieved_docs=rules
    )

    governance = governance_check(
        prediction=inference["prediction"],
        market_median=650000,
        prd_current=1.03
    )

    return {
        "prediction": inference["prediction"],
        "explanation": explanation,
        "governance": governance,
        "model_id": inference["model_id"]
    }