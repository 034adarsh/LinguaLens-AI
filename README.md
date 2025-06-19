# 🌐 LinguaLens AI Translator

Welcome to **LinguaLens AI Translator**, a powerful and user-friendly web application that breaks language barriers by translating your files (TXT, PDF, XLSX, CSV) into multiple languages effortlessly! Powered by advanced AI, this app is designed to make translation accessible to everyone, with a sleek interface that adapts to light and dark themes.

[**Try it Live! 🚀**](https://lingualens-ai.streamlit.app/)

![LinguaLens AI Translator Preview](lingualens-ui.png)  
*(Note: Replace `lingualens-ui.png` with the actual file name after uploading your UI screenshot!)*

---

## ✨ Features

- **Multi-Language Support**: Translate into 10+ languages including English, Spanish, French, German, and more!
- **File Format Flexibility**: Supports TXT, PDF, XLSX, and CSV files.
- **Theme Adaptability**: Seamlessly switches between light and dark modes for a personalized experience.
- **User-Friendly**: Intuitive interface with a "Toggle Theme" feature and clear feedback.
- **Restrictions**: Handles files up to 1MB and text content up to 5,000 characters per request for optimal performance.

---

## 🛠️ Getting Started

### Prerequisites

- Python 3.13
- Pip (Python package manager)

### Installation

```bash
git clone https://github.com/034adarsh/LinguaLens-Backend.git
cd LinguaLens-Backend
```

Create a virtual environment and activate it:

```bash
python3.13 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the app locally:

```bash
streamlit run app.py
```

Open your browser and visit `http://localhost:8501` to use the app.

---

## 🚀 Deployment

The app is deployed on Streamlit Cloud:  
🔗 [https://lingualens-ai.streamlit.app/](https://lingualens-ai.streamlit.app/)

To redeploy or modify:
- Push changes to the GitHub repository.
- The Streamlit Cloud app will automatically rebuild.

---

## 📄 Usage

1. Upload a file (TXT, PDF, XLSX, or CSV) under 1MB.
2. Select your target language from the dropdown.
3. Click "Translate Now!" to process the file.
4. Download the translated file or the original (if translation fails, a warning is shown).

---

## ⚠️ Limitations

- **File Size**: Maximum 1MB per file.
- **Text Limit**: Up to 5,000 characters per translation request.
- **PDF Support**: Scanned PDFs may not translate due to unextractable text.

---

## 🤝 Contribute

Contributions are welcome! Feel free to open issues or submit pull requests to enhance the app.

---

## 📬 Contact

Have questions or feedback? Reach out to me:

- 📧 Email: [adarsh36jnp@gmail.com](mailto:adarsh36jnp@gmail.com)
- 💼 LinkedIn: [Adarsh Kumar Singh](https://www.linkedin.com/in/adarsh-kumar-singh-data/)

Built by: **Adarsh Singh**

---

## 🙏 Acknowledgments

Built with ❤️ using [Streamlit](https://streamlit.io/), [deep-translator](https://pypi.org/project/deep-translator/), and assisted by xAI’s Grok-3.

Special thanks to the open-source community for the tools that power this project.
