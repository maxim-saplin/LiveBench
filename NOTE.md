Run local

```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model gemma-2-9b-it@iq4_xs --bench-name live_bench/instruction_following --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```s

Show results

```
python show_livebench_result.py --bench-name live_bench/instruction_following/summarize --model-list gemma-2-9b-it@iq4_xs                                             
```

## Results

Using release 2024-11-25
{'instruction_following': ['summarize']}
loaded  50  questions

########## All Tasks ##########
task                  summarize
model                          
gemma-2-9b-it@iq4_xs      57.75

########## All Groups ##########
category              average  instruction_following
model  