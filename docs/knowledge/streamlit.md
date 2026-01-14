Here's how to run your Streamlit app:

## **Basic Command**

```bash
streamlit run app.py
```

- Start the Streamlit server
- Automatically open your default browser to `http://localhost:8501`
- Display your Chess Analysis Dashboard

---

## **Step-by-Step Setup (First Time)**

### **1. Navigate to Your Project Directory**
```bash
cd path/to/chess_dashboard
```

### **2. Create Virtual Environment (Recommended)**

**Using venv:**
```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```



### **3. Install Dependencies**

**Option B: Using uv (if you have it)**
```bash
uv sync
```

### **4. Run the App**
```bash
streamlit run app.py
```

---


## **Using uv**
```bash
uv run streamlit run app.py
```

---

## **What You'll See**

When you run the command, you'll see output like:

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.1.x:8501
```

The browser should open automatically to the Local URL.

---


## **Stopping the App**

Press `Ctrl + C` in the terminal where the app is running.

