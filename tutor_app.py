import streamlit as st
import google.generativeai as genai

# --- Page Configuration ---
st.set_page_config(
    page_title="Adaptive AI Tutor",
    page_icon="🎓",
    layout="wide"
)

# --- The Core Prompt Template ---
# This is the refined prompt we developed, now as a configurable string.
PROMPT_TEMPLATE = """
**I. The Persona and Role**

You are an expert Computer Science teaching assistant and study partner for the university-level course, "{class_name}". Your persona is encouraging, precise, and deeply knowledgeable. You are not just a question-answerer; you are a guide. Your goal is to help me, the student, achieve true mastery of the course material in preparation for an exam. You will maintain a positive and motivational tone throughout our interaction.

**II. The Initial Knowledge Base & Starting Point**

You are being brought into an ongoing, adaptive study session. Your first task is to absorb the provided context to continue the session seamlessly.

**Your initial context consists of:**

1.  **My Learning Materials:** I have provided a set of files for context named: {file_names_str}.
2.  **My Core Topic List:** The following is a list of the core topics I need to master for my exam:
{topic_list}

**Your first action is to analyze this context to establish a baseline understanding of my current knowledge state. Use this to determine the initial set of "Mastered Topics" and "Working Topics". Do not generate a study guide or start with an easy quiz. We are jumping directly into the core learning loop.**

**III. The Core Interaction Loop: The Adaptive Quiz System**

After analyzing the initial context, you will begin generating practice quizzes according to the following iterative loop.

**A. Quiz Generation:**

1.  Generate a practice quiz for me. Quizzes should be short (5-7 questions) and contain a mix of formats suitable for the subject. Quizzes should contain MCQ (Multiple Choice Questions) and FRQ (Free Response Questions).
2.  **Difficulty & Content Strategy:** All quizzes will be of a consistent, higher difficulty (e.g., 7/10), designed to test nuanced understanding. You must track my performance on a topic-by-topic basis to categorize topics into "Mastered", "Working", and "New". Each quiz must follow this distribution: **~20% Mastered, ~60% Working, and ~20% New Topics.** You must explicitly state when you are using this adaptive strategy.
3.  **Question Formats:** Use diverse formats like Scenario Analysis, Spot the Flaw, Compare and Contrast, and Justify the 'Why'.

**B. Grading and Feedback:**

1.  I will provide my answers. You will grade them meticulously, providing a score.
2.  For each question, provide a detailed explanation for the correct answer. Acknowledge the reasoning in my answers, even if they are incorrect.
3.  After grading, provide a brief, encouraging "Final Score & Summary".

**IV. Special Commands and Meta-Interaction**

1.  At any time, I can ask for a "Progress Report." You will then synthesize all our quiz interactions and provide a summary of my progress.
2.  I will provide feedback on your performance, and you must incorporate it into your subsequent actions.

**V. The Goal State**

Our interaction is successful when I have achieved a perfect score on three consecutive quizzes. At that point, you can congratulate me and conclude the session.

**Your first message to me should be a brief, welcoming greeting, confirming you have understood the context and are ready to begin with the first targeted quiz.**
"""

# --- App Layout and Logic ---

st.title("🎓 Adaptive AI Tutor Generator")
st.markdown("Configure your personalized tutor using the sidebar, upload your course materials, and start learning!")

# --- Sidebar for User Inputs ---
with st.sidebar:
    st.header("Tutor Configuration")
    
    # API Key Input
    api_key = st.text_input("Enter your Gemini API Key", type="password")
    
    # Class and Topic Inputs
    class_name = st.text_input("Course Name", value="CSE 130: Principles of Computer Systems Design")
    topic_list = st.text_area(
        "Core Topics List",
        value="""- Performance: Amdahl's Law, Latency vs. Throughput
- Caching & Memory: LRU, FIFO, Clock, Associativity, Write-Through/Back
- Concurrency: pthreads, Mutexes, Condition Variables, Semaphores, Deadlock
- System Organization: Hard/Soft Modularity, RPCs
- Low-Level Details: "Find the Bugs" in C I/O, Critical Sections""",
        height=250
    )
    st.markdown("---")
    st.info("Your API key is used only for this session and is not stored.")

# --- Main Page Content ---
main_container = st.container()

with main_container:
    st.header("1. Upload Your Course Materials")
    uploaded_files = st.file_uploader(
        "Upload past quizzes, notes, or problem sets (PDF, TXT, etc.)",
        accept_multiple_files=True
    )

    st.header("2. Start Your Tutoring Session")
    if st.button("🚀 Generate Tutor"):
        if not api_key:
            st.error("Please enter your Gemini API Key in the sidebar.")
        elif not class_name or not topic_list:
            st.error("Please provide the Course Name and Topic List.")
        else:
            with st.spinner("Configuring your personal AI tutor... This may take a moment."):
                try:
                    # Configure the Generative AI library
                    genai.configure(api_key=api_key)

                    # Get names of uploaded files for the prompt
                    file_names = [file.name for file in uploaded_files]
                    if not file_names:
                        file_names_str = "No files provided. Using topic list only."
                    else:
                        file_names_str = ", ".join(file_names)

                    # Format the final prompt
                    final_prompt = PROMPT_TEMPLATE.format(
                        class_name=class_name,
                        topic_list=topic_list,
                        file_names_str=file_names_str
                    )

                    # Initialize the model and chat
                    model = genai.GenerativeModel('gemini-2.5-flash-preview-05-20')
                    chat = model.start_chat(history=[])
                    
                    # Send the system prompt to initialize the tutor
                    # This is the key step to set the context for the entire conversation.
                    initial_response = chat.send_message(final_prompt)
                    
                    # Store the chat session and initial messages in Streamlit's session state
                    st.session_state.gemini_chat = chat
                    st.session_state.messages = [{"role": "assistant", "content": initial_response.text}]
                    
                    st.success("Tutor generated successfully! You can now start chatting below.")

                except Exception as e:
                    st.error(f"An error occurred: {e}")
                    st.info("Please check your API key and ensure it has access to the Gemini 1.5 Pro model.")

# --- Chat Interface ---
if "messages" in st.session_state:
    st.header("💬 Chat with Your Tutor")
    
    # Display existing messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Get new user input
    if prompt := st.chat_input("Ask your tutor for a quiz, or answer its questions..."):
        # Add user message to session state and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Send message to Gemini and get response
        try:
            chat_session = st.session_state.gemini_chat
            with st.spinner("The tutor is thinking..."):
                response = chat_session.send_message(prompt)
            
            # Add AI response to session state and display it
            st.session_state.messages.append({"role": "assistant", "content": response.text})
            with st.chat_message("assistant"):
                st.markdown(response.text)

        except Exception as e:
            st.error(f"An error occurred while communicating with the AI: {e}")
