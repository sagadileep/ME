import streamlit as st

st.title("ME")
st.write("Your mind, understood. And it belongs to you.")

name = st.text_input("What's your name?")
choice = st.radio(
    "A new restaurant. The menu has a dish you have never heard of.",
    ["Order the unknown dish", "Order the restaurant's special",
     "Order a favourite you know", "It depends"],
    index=None,
)

if name and choice:
    st.success(f"Thanks {name}! You chose: {choice}")