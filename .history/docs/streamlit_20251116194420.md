Here's how to run your Streamlit app:

## **Basic Command**

```bash
streamlit run app.py
```

That's it! This will:
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

**Using conda:**
```bash
conda create -n chess_env python=3.10
conda activate chess_env
```

### **3. Install Dependencies**

**Option A: Using pip**
```bash
pip install -r requirements.txt
```

**Option B: Using uv (if you have it)**
```bash
uv sync
```

### **4. Run the App**
```bash
streamlit run app.py
```

---

## **Advanced Options**

### **Specify Port**
```bash
streamlit run app.py --server.port 8502
```

### **Run Without Auto-Opening Browser**
```bash
streamlit run app.py --server.headless true
```

### **Enable Development Mode (Auto-reload)**
```bash
streamlit run app.py --server.runOnSave true
```

### **Run on Network (Access from Other Devices)**
```bash
streamlit run app.py --server.address 0.0.0.0
```

### **Using uv**
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

## **Troubleshooting**

### **"streamlit: command not found"**
```bash
# Install streamlit
pip install streamlit

# Or verify installation
pip show streamlit
```

### **"Module not found" errors**
```bash
# Reinstall all dependencies
pip install -r requirements.txt
```

### **Port Already in Use**
```bash
# Use a different port
streamlit run app.py --server.port 8502
```

### **App Not Opening in Browser**
- Manually navigate to: `http://localhost:8501`
- Check firewall settings
- Try: `streamlit run app.py --server.headless false`

### **Virtual Environment Issues**
```bash
# Make sure venv is activated (you should see (venv) in terminal)
# If not, activate it:
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

---

## **Complete First-Time Setup Example**

```bash
# 1. Navigate to project
cd chess_dashboard

# 2. Create virtual environment
python -m venv venv

# 3. Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate     # Windows

# 4. Install dependencies
pip install -r requirements.txt

# 5. Run the app
streamlit run app.py
```

---

## **Stopping the App**

Press `Ctrl + C` in the terminal where the app is running.

---

## **Quick Test**

To verify everything works:

1. Run `streamlit run app.py`
2. Enter a Chess.com username (try "Magnus" or "Hikaru")
3. Click "Fetch All Games" or "Fetch Date Range"
4. Explore the dashboard!

The app will automatically create `data/` and `models/` directories as needed.