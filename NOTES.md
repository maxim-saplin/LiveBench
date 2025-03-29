Run local

```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model gemma-2-9b-it@iq4_xs --bench-name live_bench/instruction_following --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```s

Show results

```
python show_livebench_result.py --bench-name live_bench/instruction_following/summarize --model-list gemma-2-9b-it@iq4_xs                                             
```

## Results

########## All Tasks ##########
task                  AMPS_Hard  LCB_generation  coding_completion  connections  ...  tablereformat  typos  web_of_lies_v2  zebra_puzzle
model                                                                            ...                                                    
gemma-2-9b-it@iq4_xs       34.0          25.641               20.0       23.333  ...           68.0   26.0            12.0           6.0

[1 rows x 18 columns]

########## All Groups ##########
category              average  coding  data_analysis  instruction_following  language  math  reasoning
model                                                                                                 
gemma-2-9b-it@iq4_xs     29.9    22.8           41.6                   62.7      24.1  20.2        8.0