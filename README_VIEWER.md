# LiveBench Results Viewer

A Streamlit application for easily navigating and comparing model answers and evaluation results from LiveBench.

## Features

- Browse model responses by category, task, and model
- View prompt/question. model answers and corresponding scores
- Compare performance across different models
- View detailed statistics for each model's performance on a task

## How to Use

Do not use in the same venv as LiveBench! Create a separate Python 3.10+ venv for the Streamlit app!

1. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

2. The app will open in your browser at `http://localhost:8501`

3. Navigation:
   - Use the sidebar to select a category (e.g., language, reasoning, math)
   - Select a specific task within that category
   - Choose which view you want to see:
     - **Model Answers**: View individual model responses and scores
     - **Model Comparison**: Compare performance across models

4. In the "Model Answers" tab:
   - Select a model from the dropdown
   - View the model's overall statistics for the selected task
   - Choose a specific question to see the model's response and score

5. In the "Model Comparison" tab:
   - View a table of all models' performance statistics
   - Compare different models' answers to the same question

## Data Structure

The app expects data to be organized in the following structure:
```
livebench/data/live_bench/
├── category1/
│   ├── task1/
│   │   ├── model_answer/
│   │   │   ├── model1.jsonl
│   │   │   └── model2.jsonl
│   │   └── model_judgment/
│   │       └── ground_truth_judgment.jsonl
│   └── task2/
│       └── ...
├── category2/
│   └── ...
```

## Requirements

- Python 3.10+
- Streamlit
- Pandas

Install dependencies with:
```
pip install streamlit pandas
``` 