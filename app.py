import streamlit as st
import os
import json
import glob
from collections import defaultdict
import pandas as pd
import re

st.set_page_config(
    page_title="LiveBench Results Viewer",
    page_icon="📊",
    layout="wide"
)

# Define paths
BASE_DATA_PATH = "livebench/data/live_bench"

# Custom CSS
st.markdown("""
<style>
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .model-response {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .model-info {
        font-size: 0.9em;
        color: #666;
    }
    .question-box {
        background-color: #e8f4f8;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
        border-left: 5px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

def load_jsonl(file_path):
    """Load data from a JSONL file."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data

def get_categories():
    """Get all categories from the data folder."""
    return sorted([d for d in os.listdir(BASE_DATA_PATH) if os.path.isdir(os.path.join(BASE_DATA_PATH, d))])

def get_tasks(category):
    """Get all tasks for a specific category."""
    category_path = os.path.join(BASE_DATA_PATH, category)
    return sorted([d for d in os.listdir(category_path) if os.path.isdir(os.path.join(category_path, d))])

def get_models(category, task):
    """Get all models for a specific task."""
    models = set()
    task_path = os.path.join(BASE_DATA_PATH, category, task, "model_answer")
    if os.path.exists(task_path):
        for file in os.listdir(task_path):
            if file.endswith(".jsonl"):
                models.add(file.split(".")[0])
    return sorted(list(models))

def get_judgments(category, task):
    """Get judgment data for a specific task."""
    judgments = {}
    judgment_path = os.path.join(BASE_DATA_PATH, category, task, "model_judgment", "ground_truth_judgment.jsonl")
    if os.path.exists(judgment_path):
        judgment_data = load_jsonl(judgment_path)
        for item in judgment_data:
            key = (item.get("question_id"), item.get("model"))
            judgments[key] = item.get("score", None)
    return judgments

def get_all_question_answers(category, task, question_id):
    """Get all model answers for a specific question."""
    models = get_models(category, task)
    model_answers = {}
    
    for model in models:
        answer_file = os.path.join(BASE_DATA_PATH, category, task, "model_answer", f"{model}.jsonl")
        if os.path.exists(answer_file):
            answers = load_jsonl(answer_file)
            for answer in answers:
                if answer.get("question_id") == question_id:
                    model_answers[model] = answer
                    break
    
    return model_answers

def get_model_stats(category, task, model):
    """Get score statistics for a model on a task."""
    judgments = get_judgments(category, task)
    
    model_scores = [score for (qid, model_name), score in judgments.items() if model_name == model]
    
    if model_scores:
        return {
            "mean": sum(model_scores) / len(model_scores),
            "min": min(model_scores),
            "max": max(model_scores),
            "count": len(model_scores)
        }
    return None

def get_question_text(category, task, question_id):
    """Get the original question text for a given question ID."""
    # Look for question.jsonl file in the category/task directory
    question_file_path = os.path.join(BASE_DATA_PATH, category, task, "question.jsonl")
    
    if os.path.exists(question_file_path):
        questions = load_jsonl(question_file_path)
        for question in questions:
            if question.get("question_id") == question_id:
                # Extract the actual prompt/question text
                return question.get("turns", None)
    
    return None


def format_question_content(question_data):
    """Format the question content for display with better structure."""
    return "\n\n".join(question_data)

def extract_code(text):
    """Extract Python code from text that might have markdown code blocks."""
    if not text:
        return text
    
    # First check for Python code blocks with language specifier
    python_pattern = r'```(?:python|py)\s*([\s\S]*?)```'
    matches = re.findall(python_pattern, text)
    
    if matches:
        return '\n\n'.join(matches)
    
    # Then check for any code blocks
    code_pattern = r'```([\s\S]*?)```'
    matches = re.findall(code_pattern, text)
    
    if matches:
        return '\n\n'.join(matches)
    
    # If no code blocks found, return original text
    return text

def clean_model_response(text):
    """Clean the response from a model to make it more readable."""
    if not text:
        return ""
        
    # Remove excessive newlines (more than 2 in a row)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove <think>...</think> blocks used by some models for internal reasoning
    text = re.sub(r'<think>[\s\S]*?</think>', '', text)
    
    # Remove "Here is the solution" preambles that often appear in coding answers
    text = re.sub(r'(?i)^(here\'s|here is)(\s+the)?(\s+solution|\s+code|\s+answer).*?:\s*', '', text)
    text = re.sub(r'(?i)^(my solution|my approach|solution|approach).*?:\s*', '', text)
    
    return text.strip()

def format_model_response(selected_answer, category, task):
    """Format the model response for better display."""
    response_content = []
    model_text = ""
    
    # First, try to get the raw model output text from common fields
    if "text" in selected_answer:
        model_text = selected_answer["text"]
    elif "model_output" in selected_answer:
        model_text = selected_answer["model_output"]
    elif "choices" in selected_answer and selected_answer["choices"]:
        for choice in selected_answer["choices"]:
            if "text" in choice:
                model_text = choice["text"]
                break
            elif "turns" in choice and choice["turns"]:
                model_text = choice["turns"][0]
                break
    
    # For coding tasks, prioritize showing code extractions
    if category == "coding":
        has_code = False
        
        # Try to extract code from the model text
        code = extract_code(model_text)
        if code and code != model_text:
            has_code = True
            # Add the full response first
            cleaned_text = clean_model_response(model_text)
            if cleaned_text:
                response_content.append({
                    "type": "text",
                    "content": cleaned_text,
                    "label": "Complete Response"
                })
            
        else:
            # If we couldn't extract distinct code, show the full response
            cleaned_text = clean_model_response(model_text)
            if cleaned_text:
                response_content.append({
                    "type": "text",
                    "content": cleaned_text,
                    "label": "Model Response"
                })
        
        # If no code was found, check different fields
        if not has_code and not response_content:
            for key, value in selected_answer.items():
                if key not in ["question_id", "model_id", "answer_id", "choices", "text", "model_output", "tstamp"] and isinstance(value, str):
                    code = extract_code(value)
                    if code and code != value:
                        response_content.append({
                            "type": "code",
                            "content": code,
                            "language": "python",
                            "label": f"Code from {key}"
                        })
                        break
    
    # For non-coding tasks, display the full response text
    else:
        cleaned_text = clean_model_response(model_text)
        if cleaned_text:
            response_content.append({
                "type": "text",
                "content": cleaned_text,
                "label": "Model Response"
            })
    
    # If we still have no content, try to parse any field that might contain the answer
    if not response_content:
        for key, value in selected_answer.items():
            if key not in ["question_id", "model_id", "answer_id", "tstamp"] and isinstance(value, str) and len(value) > 10:
                cleaned_text = clean_model_response(value)
                response_content.append({
                    "type": "text",
                    "content": cleaned_text,
                    "label": f"Content from {key}"
                })
                break
    
    return response_content

def format_judgment_explanation(judgment_data, category, task):
    """Format judgment data with explanations of the scoring criteria."""
    if not judgment_data:
        return None
        
    explanation = {}
    
    # Extract the score and relevant information
    if isinstance(judgment_data, list):
        scores = [item.get("score", "N/A") for item in judgment_data]
        avg_score = sum(float(s) for s in scores if isinstance(s, (int, float))) / len(scores) if scores else "N/A"
        explanation["score"] = avg_score
        
        # Get additional judgment details
        if judgment_data and isinstance(judgment_data[0], dict):
            for key, value in judgment_data[0].items():
                if key not in ["question_id", "answer_id", "model", "score", "turn", "tstamp", "category"]:
                    explanation[key] = value
    else:
        explanation["score"] = judgment_data.get("score", "N/A")
        
        # Get additional judgment details
        for key, value in judgment_data.items():
            if key not in ["question_id", "answer_id", "model", "score", "turn", "tstamp", "category"]:
                explanation[key] = value
        
    return explanation

def get_test_case_results(category, task, question_id, model):
    """Try to extract test case results for coding tasks."""
    if category != "coding":
        return None
        
    # Look for test case results metadata in the judgment file
    judgment_path = os.path.join(BASE_DATA_PATH, category, task, "model_judgment", "ground_truth_judgment.jsonl")
    if not os.path.exists(judgment_path):
        return None
        
    try:
        judgments = load_jsonl(judgment_path)
        for judgment in judgments:
            if judgment.get("question_id") == question_id and judgment.get("model") == model:
                if "metadata" in judgment:
                    return judgment["metadata"]
                # If metadata isn't in the judgment, we can't show test case results
                return None
    except:
        pass
    
    # If we failed to extract from the judgment file, try to look in the evaluation results
    eval_path = os.path.join(BASE_DATA_PATH, category, task, "evaluation_results")
    if not os.path.exists(eval_path):
        return None
        
    try:
        for file in os.listdir(eval_path):
            if file.endswith(".json") and model.lower() in file.lower():
                with open(os.path.join(eval_path, file), 'r') as f:
                    eval_data = json.load(f)
                    if question_id in eval_data:
                        return eval_data[question_id]
    except:
        pass
        
    return None

def main():
    st.title("LiveBench Results Viewer")
    
    # Sidebar for navigation
    st.sidebar.header("Navigation")
    
    # Get available categories
    categories = get_categories()
    selected_category = st.sidebar.selectbox("Select Category", categories)
    
    if selected_category:
        # Get available tasks for the selected category
        tasks = get_tasks(selected_category)
        selected_task = st.sidebar.selectbox("Select Task", tasks)
        
        if selected_task:
            tab1, tab2 = st.tabs(["Model Answers", "Model Comparison"])
            
            with tab1:
                # Get available models for the selected task
                models = get_models(selected_category, selected_task)
                selected_model = st.selectbox("Select Model", models, key="model_selector")
                
                if selected_model:
                    # Load model answers
                    answer_file = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "model_answer", f"{selected_model}.jsonl")
                    
                    if os.path.exists(answer_file):
                        # Load answers and judgments
                        answers = load_jsonl(answer_file)
                        judgments = get_judgments(selected_category, selected_task)
                        
                        # Display model statistics
                        stats = get_model_stats(selected_category, selected_task, selected_model)
                        if stats:
                            st.subheader(f"Model Performance: {selected_model}")
                            col1, col2, col3 = st.columns(3)
                            col1.metric("Average Score", f"{stats['mean']:.2f}")
                            col2.metric("Questions Evaluated", stats['count'])
                            col3.metric("Score Range", f"{stats['min']:.2f} - {stats['max']:.2f}")
                        
                        # Display question selector
                        question_ids = [a.get("question_id") for a in answers]
                        question_options = [f"Question {i+1} (ID: {qid[:8]}...)" for i, qid in enumerate(question_ids)]
                        selected_index = st.selectbox("Select Question", range(len(question_ids)), 
                                                    format_func=lambda i: question_options[i])
                        
                        if selected_index is not None and answers:
                            selected_answer = answers[selected_index]
                            question_id = selected_answer.get("question_id")
                            
                            # Get score for this question
                            score = judgments.get((question_id, selected_model))
                            
                            # Try to get the original question
                            question_data = get_question_text(selected_category, selected_task, question_id)
                            
                            # Display results
                            col1, col2 = st.columns([1, 1])
                            
                            with col1:
                                st.subheader("Question Information")
                                st.text(f"Question ID: {question_id}")
                                st.text(f"Task: {selected_task}")
                                st.text(f"Category: {selected_category}")
                                
                                if score is not None:
                                    st.metric("Score", f"{score:.2f}")
                                
                                # Display the question content
                                st.markdown("### Prompt")
                                st.markdown(f'<div class="question-box">{format_question_content(question_data)}</div>', unsafe_allow_html=True)
                            
                            with col2:
                                st.subheader("Model Response")
                                
                                # Display model response
                                response_content = format_model_response(selected_answer, selected_category, selected_task)
                                for item in response_content:
                                    if "label" in item:
                                        st.subheader(item["label"])
                                    if item["type"] == "code":
                                        st.code(item["content"], language=item["language"])
                                    else:
                                        st.markdown(item["content"])
                                
                                # Try to find ground truth or rules
                                rules_path = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "questions")
                                rules_found = False
                                if os.path.exists(rules_path):
                                    for file in os.listdir(rules_path):
                                        if file.endswith("_rules.jsonl") or file.endswith("_rules.json"):
                                            try:
                                                rules_data = load_jsonl(os.path.join(rules_path, file))
                                                for rule in rules_data:
                                                    if rule.get("question_id") == question_id:
                                                        st.subheader("Evaluation Rules")
                                                        st.markdown(f'<div class="question-box">{json.dumps(rule, indent=2)}</div>', unsafe_allow_html=True)
                                                        rules_found = True
                                                        break
                                            except:
                                                pass
                                
                                # If no specific rules found, check if there's a ground truth judgment
                                if not rules_found:
                                    judgment_path = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "model_judgment", "ground_truth_judgment.jsonl")
                                    if os.path.exists(judgment_path):
                                        ground_truth = []
                                        judgment_data = load_jsonl(judgment_path)
                                        for item in judgment_data:
                                            if item.get("question_id") == question_id and item.get("model") == selected_model:
                                                ground_truth.append(item)
                                        
                                        if ground_truth:
                                            st.subheader("Model Evaluation")
                                            judgment_explanation = format_judgment_explanation(ground_truth, selected_category, selected_task)
                                            
                                            # Display score with explanation
                                            score = judgment_explanation.get("score", "N/A")
                                            st.metric("Score", f"{score}")
                                            
                                            if "details" in judgment_explanation:
                                                st.markdown(f"**Evaluation Details**: {judgment_explanation['details']}")
                                            
                                            # For coding tasks, try to show test case results
                                            if selected_category == "coding":
                                                test_results = get_test_case_results(selected_category, selected_task, question_id, selected_model)
                                                if test_results:
                                                    st.subheader("Test Case Results")
                                                    
                                                    # Try to parse the test results
                                                    try:
                                                        if isinstance(test_results, str):
                                                            test_results = json.loads(test_results)
                                                            
                                                        if isinstance(test_results, dict):
                                                            # Display the test results in a readable format
                                                            for test_key, test_value in test_results.items():
                                                                if isinstance(test_value, (list, dict)):
                                                                    st.json(test_value)
                                                                else:
                                                                    st.markdown(f"**{test_key}**: {test_value}")
                                                        elif isinstance(test_results, list):
                                                            # If it's a list of test results
                                                            for i, result in enumerate(test_results):
                                                                if isinstance(result, (int, bool)):
                                                                    status = "✅ Passed" if result > 0 and result != -1 and result != -2 else "❌ Failed"
                                                                    reason = ""
                                                                    if result == -1:
                                                                        reason = " (Runtime Error)"
                                                                    elif result == -2:
                                                                        reason = " (Compilation Error)"
                                                                    st.markdown(f"**Test {i+1}**: {status}{reason}")
                                                                else:
                                                                    st.markdown(f"**Test {i+1}**: {result}")
                                                    except:
                                                        st.markdown("Test case results available but could not be parsed.")
                                            
                                            # Show raw judgment data in an expander for debugging
                                            with st.expander("Raw Judgment Data"):
                                                st.json(ground_truth)
                    else:
                        st.error(f"No answer file found for model {selected_model} in task {selected_task}")
            
            with tab2:
                st.subheader("Model Comparison")
                
                # Get all models for the task
                models = get_models(selected_category, selected_task)
                judgments = get_judgments(selected_category, selected_task)
                
                # Compute statistics for each model
                model_stats = {}
                for model in models:
                    stats = get_model_stats(selected_category, selected_task, model)
                    if stats:
                        model_stats[model] = stats
                
                # Create a dataframe for display
                if model_stats:
                    data = []
                    for model, stats in model_stats.items():
                        data.append({
                            "Model": model,
                            "Avg Score": f"{stats['mean']:.3f}",
                            "Min Score": f"{stats['min']:.2f}",
                            "Max Score": f"{stats['max']:.2f}",
                            "Evaluated Questions": stats['count']
                        })
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df.sort_values(by="Avg Score", ascending=False), use_container_width=True)
                    
                    # Show a single question across all models
                    st.subheader("Compare Answers to the Same Question")
                    
                    # Get a list of all question IDs across all models
                    all_questions = set()
                    for model in models:
                        answer_file = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "model_answer", f"{model}.jsonl")
                        if os.path.exists(answer_file):
                            answers = load_jsonl(answer_file)
                            for answer in answers:
                                all_questions.add(answer.get("question_id"))
                    
                    question_id_options = sorted(list(all_questions))
                    if question_id_options:
                        selected_question_idx = st.selectbox(
                            "Select Question to Compare", 
                            range(len(question_id_options)),
                            format_func=lambda i: f"Question {i+1} (ID: {question_id_options[i][:8]}...)"
                        )
                        
                        if selected_question_idx is not None:
                            selected_question_id = question_id_options[selected_question_idx]
                            
                            # Try to get the original question
                            question_data = get_question_text(selected_category, selected_task, selected_question_id)
                            
                            # Display the original question
                            st.markdown("### Prompt")
                            st.markdown(f'<div class="question-box">{format_question_content(question_data)}</div>', unsafe_allow_html=True)
                            
                            # Display model answers section
                            with st.expander("Model Answers", expanded=True):
                                model_answers = {}
                                
                                # Collect all model answers first
                                for model_name in models:
                                    model_answer_path = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "model_answers", f"{model_name}.jsonl")
                                    
                                    if os.path.exists(model_answer_path):
                                        answers_data = load_jsonl(model_answer_path)
                                        
                                        # Find the answer for the selected question
                                        for answer in answers_data:
                                            if answer.get("question_id") == selected_question_id:
                                                model_answers[model_name] = answer
                                                break
                                
                                if model_answers:
                                    # Create columns for different models
                                    cols = st.columns(len(model_answers))
                                    
                                    # Display each model's answer
                                    for i, (model_name, answer) in enumerate(model_answers.items()):
                                        with cols[i]:
                                            # Format and display the model answer
                                            st.markdown(f"## {model_name}")
                                            response_text = answer.get("text", answer.get("model_output", ""))
                                            formatted_response = format_model_response(answer, selected_category, selected_task)
                                            
                                            if selected_category == "coding":
                                                # For coding tasks, try to extract and display code block
                                                code = extract_code(response_text)
                                                if code and code != response_text:
                                                    with st.expander("Response", expanded=True):
                                                        for item in formatted_response:
                                                            if "label" in item:
                                                                st.subheader(item["label"])
                                                            if item["type"] == "text":
                                                                st.markdown(item["content"])
                                                    with st.expander("Extracted Code", expanded=True):
                                                        st.code(code, language="python")
                                                else:
                                                    for item in formatted_response:
                                                        if "label" in item:
                                                            st.subheader(item["label"])
                                                        if item["type"] == "code":
                                                            st.code(item["content"], language=item["language"])
                                                        else:
                                                            st.markdown(item["content"])
                                            else:
                                                # For non-coding tasks, display the clean response
                                                for item in formatted_response:
                                                    if "label" in item:
                                                        st.subheader(item["label"])
                                                    if item["type"] == "code":
                                                        st.code(item["content"], language=item["language"])
                                                    else:
                                                        st.markdown(item["content"])
                                            
                                            # Display ground truth judgment if available
                                            judgment_path = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "model_judgment", "ground_truth_judgment.jsonl")
                                            if os.path.exists(judgment_path):
                                                ground_truth = []
                                                judgment_data = load_jsonl(judgment_path)
                                                for item in judgment_data:
                                                    if item.get("question_id") == selected_question_id and item.get("model") == model_name:
                                                        ground_truth.append(item)
                                                
                                                if ground_truth:
                                                    with st.expander("Model Evaluation"):
                                                        judgment_explanation = format_judgment_explanation(ground_truth, selected_category, selected_task)
                                                        
                                                        # Display score
                                                        score = judgment_explanation.get("score", "N/A")
                                                        st.metric("Score", f"{score}")
                                                        
                                                        # For coding tasks, try to show test results
                                                        if selected_category == "coding":
                                                            test_results = get_test_case_results(selected_category, selected_task, selected_question_id, model_name)
                                                            if test_results:
                                                                st.markdown("### Test Case Results")
                                                                try:
                                                                    if isinstance(test_results, str):
                                                                        test_results = json.loads(test_results)
                                                                        
                                                                    if isinstance(test_results, list):
                                                                        passed = sum(1 for r in test_results if r > 0 and r != -1 and r != -2)
                                                                        total = len(test_results)
                                                                        st.markdown(f"**Tests Passed**: {passed}/{total}")
                                                                        
                                                                        # Display individual test results
                                                                        for i, result in enumerate(test_results):
                                                                            status = "✅ Passed" if result > 0 else "❌ Failed"
                                                                            if result == -1:
                                                                                status = "⚠️ Error"
                                                                            elif result == -2:
                                                                                status = "⏱️ Timeout"
                                                                            st.markdown(f"Test {i+1}: {status}")
                                                                except Exception as e:
                                                                    st.error(f"Error parsing test results: {e}")
                                                        
                                                        # Display evaluation criteria
                                                        if "criteria" in judgment_explanation:
                                                            st.markdown(f"**Scoring Criteria**: {judgment_explanation['criteria']}")
                                                        
                                                        if "details" in judgment_explanation:
                                                            st.markdown(f"**Evaluation Details**: {judgment_explanation['details']}")
                                
                            # Display evaluation rules if available
                            rules_path = os.path.join(BASE_DATA_PATH, selected_category, selected_task, "questions")
                            if os.path.exists(rules_path):
                                for file in os.listdir(rules_path):
                                    if file.endswith("_rules.jsonl") or file.endswith("_rules.json"):
                                        try:
                                            rules_data = load_jsonl(os.path.join(rules_path, file))
                                            for rule in rules_data:
                                                if rule.get("question_id") == selected_question_id:
                                                    with st.expander("Evaluation Rules"):
                                                        st.markdown(f'<div class="question-box">{json.dumps(rule, indent=2)}</div>', unsafe_allow_html=True)
                                                    break
                                        except:
                                            pass
                            else:
                                st.info("No model comparison data available for this task.")

if __name__ == "__main__":
    main() 