- Run against local LM Studio endpoint:
```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model gemma-2-9b-it@iq4_xs --bench-name live_bench/instruction_following --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```

- Use model alias (display name) and change temp:
```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model google_gemma-3-4b-it --model-display-name google_gemma-3-4b-it@temp03 --force-temperature 0.3  --bench-name live_bench --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```

- Randomizing prompts by adding Heloe xyzq, {datetime} to every prompt head:
```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model google_gemma-3-4b-it --model-display-name google_gemma-3-4b-it@randomized#2 --randomize-prompt --bench-name live_bench --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```

-Randomize prompts by adding 1% of typos (randomly replacing latters with 1% probability):
```
export EMPTY_API_KEY=EMPTY && python run_livebench.py --model google_gemma-3-4b-it --model-display-name google_gemma-3-4b-it@noise --add-noise --bench-name live_bench --api-base http://localhost:1234/v1 --api-key-name EMPTY_API_KEY
```

- Show results
```
python show_livebench_result.py --bench-name live_bench                                         
```

## Results

Local models via LM Studio 0.3.14, llama.cpp CUDA 1.23.1 and RTX 4090

```
category                          average  coding  data_analysis  instruction_following  language  math  reasoning
model                                                                                                             
google_gemma-3-27b-it@iq4_xs         50.7    36.9           52.8                   82.1      31.9  53.5       47.3
google_gemma-3-12b-it@iq4_xs         43.6    31.3           45.3                   81.4      25.1  38.5       40.0
gemma-2-27b-it@iq4_xs#3              39.9    36.6           48.1                   68.0      29.9  25.7       31.3
gemma-2-27b-it@iq4_xs                39.8    36.6           48.1                   67.6      29.5  25.0       32.0
gemma-2-27b-it@iq4_xs#2              39.6    35.9           48.1                   67.6      29.9  24.0       32.0
gemma-2-27b-it@iq4_xs@randomized     39.4    35.9           49.6                   68.6      28.6  25.7       28.0
gemma-2-27b-it@iq4_xs@temp03         39.3    34.7           48.7                   67.8      30.5  25.9       28.0
gemma-2-27b-it@iq4_xs@temp10#2       38.8    33.3           49.7                   66.0      28.9  25.6       29.3
gemma-2-27b-it@iq4_xs@temp10         36.8    32.7           46.3                   63.5      27.9  24.3       26.0
gemma-2-27b-it@iq4_xs@noise          33.1    34.3           26.5                   60.6      26.4  24.5       26.0
gemma-2-27b-it@iq4_xs@noise#3        32.8    34.4           22.5                   63.7      23.1  25.1       28.0
gemma-2-27b-it@iq4_xs@noise#4        32.0    30.7           25.6                   59.9      25.1  25.5       25.3
google_gemma-3-4b-it@temp03#3        31.9    21.9           36.5                   65.2       8.2  31.4       28.0
google_gemma-3-4b-it@temp10          31.7    22.2           36.4                   67.2       6.9  30.1       27.3
google_gemma-3-4b-it@q8_0            31.7    21.5           37.8                   67.1       8.5  33.1       22.0
google_gemma-3-4b-it@temp03          31.7    23.5           35.5                   64.6       8.7  30.9       26.7
gemma-2-27b-it@iq4_xs@noise#2        31.6    33.0           23.7                   62.5      23.6  24.2       22.7
google_gemma-3-4b-it@temp03#2        31.4    23.5           35.6                   65.1       8.8  29.2       26.0
google_gemma-3-4b-it#5               31.3    24.5           35.2                   66.4      10.3  28.8       22.7
google_gemma-3-4b-it                 31.0    23.9           35.9                   62.6       7.6  29.1       26.7
google_gemma-3-4b-it#4               30.8    22.9           36.0                   63.6       7.6  29.5       25.3
google_gemma-3-4b-it#2               30.5    24.5           36.6                   62.3       9.0  29.9       20.7
google_gemma-3-4b-it@randomized      30.3    21.9           34.0                   70.0       9.2  29.5       17.3
google_gemma-3-4b-it#3               30.1    24.5           34.6                   62.6       9.0  29.1       20.7
gemma-2-9b-it@iq4_xs                 29.9    22.8           41.6                   62.7      24.1  20.2        8.0
google_gemma-3-4b-it@noise#3         27.9    18.9           18.9                   67.2       9.6  23.9       28.7
google_gemma-3-4b-it@noise#4         27.3    20.5           17.9                   63.6       7.1  28.3       26.0
google_gemma-3-4b-it@noise#6         27.0    18.0           18.3                   65.1       6.6  29.6       24.7
google_gemma-3-4b-it@noise#2         26.9    17.6           19.3                   61.9       6.5  29.5       26.7
google_gemma-3-4b-it@noise#5         26.6    20.9           19.7                   61.2       5.9  26.7       25.3
google_gemma-3-4b-it@noise           26.4    18.3           19.3                   63.0       8.1  30.3       19.3
```