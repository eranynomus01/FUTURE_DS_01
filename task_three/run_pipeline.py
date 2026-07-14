import subprocess
import sys
import os

def run_script(script_path):
    print(f"\n==========================================")
    print(f"Running script: {script_path}")
    print(f"==========================================")
    
    result = subprocess.run([sys.executable, script_path], capture_output=False, text=True)
    if result.returncode != 0:
        print(f"Error executing {script_path}. Exiting pipeline.")
        sys.exit(result.returncode)
    else:
        print(f"Successfully completed: {script_path}")

if __name__ == "__main__":
    # Ensure current working directory is workspace root/task_three
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the data pipeline scripts in order
    run_script("scripts/generate_data.py")
    run_script("scripts/clean_data.py")
    run_script("scripts/analyze_data.py")
    run_script("scripts/test_pipeline.py")
    
    print("\n==========================================")
    print("ALL PIPELINE SCRIPTS EXECUTED SUCCESSFULLY!")
    print("==========================================")
