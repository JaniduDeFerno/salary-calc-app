import os
import webbrowser
import time

def launch():
    # Start Streamlit in a new CMD window so it stays running!
    os.system('start cmd /k "streamlit run Home.py"')
    time.sleep(2)
    webbrowser.open("http://localhost:8501")
    input("Press Enter to exit this launcher window...")

if __name__ == "__main__":
    launch()
