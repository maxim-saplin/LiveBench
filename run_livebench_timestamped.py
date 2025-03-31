#!/usr/bin/env python3
"""
LiveBench runner script with timestamped model display names
Run multiple evaluations with different settings and track results
"""

import os
import subprocess
import datetime
import argparse

# Global variables - customize these
MODEL = "gemma-2-9b-it@iq4_xs"
FEATURE = "temperature"  # This could be "temp0.7" or whatever you're testing

def run_livebench_with_timestamp(bench_name, api_base, api_key_name, temperature=None, max_tokens=None):
    # Generate timestamp in MM-dd-hh-mm format
    timestamp = datetime.datetime.now().strftime("%m-%d-%H-%M")
    
    # Create display name with format {model}-{MM-dd-hh-mm}-{feature}
    temp_str = f"temp{temperature}" if temperature is not None else "default"
    feature_value = f"{FEATURE}-{temp_str}"
    model_display_name = f"{MODEL}-{timestamp}-{feature_value}"
    
    print(f"Running LiveBench with display name: {model_display_name}")
    
    # Build the LiveBench command
    cmd = [
        "python", "run_livebench.py",
        "--model", MODEL,
        "--model-display-name", model_display_name,
        "--bench-name", bench_name,
        "--api-base", api_base,
        "--api-key-name", api_key_name
    ]
    
    # Add optional parameters if provided
    if temperature is not None:
        cmd.extend(["--force-temperature", str(temperature)])
    
    if max_tokens is not None:
        cmd.extend(["--max-tokens", str(max_tokens)])
    
    # Run the command
    print("Executing command:", " ".join(cmd))
    result = subprocess.run(cmd, check=True)
    
    if result.returncode == 0:
        print(f"LiveBench run completed successfully for {model_display_name}")
        
        # Show results
        show_cmd = [
            "python", "show_livebench_result.py",
            "--bench-name", bench_name,
            "--model-list", model_display_name
        ]
        
        print("Getting results with command:", " ".join(show_cmd))
        subprocess.run(show_cmd, check=True)
        
        return model_display_name
    else:
        print(f"LiveBench run failed for {model_display_name}")
        return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LiveBench with timestamped model names")
    parser.add_argument("--bench-name", type=str, default="live_bench/instruction_following",
                       help="The benchmark to run")
    parser.add_argument("--api-base", type=str, default="http://localhost:1234/v1",
                       help="API base URL")
    parser.add_argument("--api-key-name", type=str, default="EMPTY_API_KEY",
                       help="Name of environment variable containing API key")
    parser.add_argument("--temperature", type=float, default=None,
                       help="Temperature value to use")
    parser.add_argument("--max-tokens", type=int, default=None,
                       help="Max tokens to generate")
    
    args = parser.parse_args()
    
    # Run LiveBench with the specified parameters
    model_display_name = run_livebench_with_timestamp(
        args.bench_name,
        args.api_base,
        args.api_key_name,
        args.temperature,
        args.max_tokens
    )
    
    print(f"Completed benchmark run with display name: {model_display_name}") 