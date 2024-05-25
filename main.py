from playwright.async_api import async_playwright
import time
import streamlit as st
import json
import asyncio
import google.generativeai as genai
import random
import os

wait_time = random.uniform(4, 5)

safe = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_NONE",
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_NONE",
    },
    ]

async def save_session_to_json(url):

    async with async_playwright() as p:
        
        browser = await p.firefox.launch(headless=False,channel="firefox")
        context = await browser.new_context()
        page = await context.new_page()
        await page.bring_to_front()
        await page.goto(url)

        while True:
            svg_selector = '.css-1g0p6jv-StyledInboxIcon'
            svg_element = await page.query_selector(svg_selector)
            if svg_element is not None:
                break
            else:
                time.sleep(2)
                pass

        session_cookies = await context.cookies()
        output_file = f'assets/session.json'
        with open(output_file, 'w') as json_file:
            json.dump(session_cookies, json_file, indent=2)

        await browser.close()
        st.success("Login was Successfully Saved.")

async def main(proxy_server, proxy_port, proxy_username, proxy_password, proxy, prompt):

    genai.configure(api_key='keyhere')
    model = genai.GenerativeModel('models/gemini-pro')
    chat = model.start_chat()

    async with async_playwright() as p:

        if proxy == "Yes":
            browser = await p.firefox.launch(
                proxy={
                        'server': f"{proxy_server}:{proxy_port}",
                        'username': proxy_username,
                        'password': proxy_password
                    },
                headless=True, channel="firefox")
        elif proxy == "No":
            browser = await p.firefox.launch(headless=True, channel="firefox")

        context = await browser.new_context()
        cookies_file = f'assets/session.json'
        with open(cookies_file, 'r') as json_file:
                saved_cookies = json.load(json_file)

        await context.add_cookies(saved_cookies)
        page = await context.new_page()
        with open ("assets/creators list.txt", 'r') as file:
            creators_list = file.read().splitlines()

        count = 0

        while True:

            for creator in creators_list:
                await page.goto(f"https://www.tiktok.com/@{creator}")
                await page.wait_for_load_state()
                time.sleep(wait_time)

                div_selector = '.css-x6y88p-DivItemContainerV2'
                divs = await page.query_selector_all(div_selector)

                for div in divs:
                    inner_text = await div.inner_text()
                    if "Pinned" not in inner_text:
                        await div.click()
                        break
                    else:
                        pass

                time.sleep(wait_time)

                with open ("assets/already_commented_on.txt", 'r') as file:
                    already_commented_on = file.read().splitlines()

                button_selector = 'button[data-e2e="browse-sound"]'

                if count == 0:
                    await page.click(button_selector)
                    time.sleep(3)
                    count = count + 1

                button_selector = '.css-xakz2y-ButtonActionItem'
                await page.click(button_selector)
                time.sleep(3)

                if page.url not in already_commented_on:
                    caption = await page.inner_text('.css-1d7krfw-DivOverflowContainer')
                    with open ("assets/already_commented_on.txt", 'a') as file:
                        file.write(f"{page.url}\n")
                    game_start = f"This {caption} is the caption of a Tiktok Post, Respond to it as if you were commenting on a post with this Caption, {prompt}"
                    element = page.locator("div[role='textbox']")
                    response = chat.send_message(game_start, safety_settings=safe)
                    await element.type(response.text)
                    time.sleep(wait_time)
                    await page.keyboard.press("Enter")
                    time.sleep(wait_time)
                    st.info(f"Commented on Post {page.url} of Creator {creator}.")
                else:
                    st.warning(f"No New Posts by {creator}.")

            st.warning("Waiting for 10 min before checking for new posts again.")
            time.sleep(600)

if __name__ == "__main__":

    st.set_page_config(
    page_title="Tiktok Commenter",
    page_icon="🚀",
    )

    hide_streamlit_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    </style>
    """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True) 
    st.markdown('<style> .stDeployButton { display: none; } </style>', unsafe_allow_html=True)

    st.title("TikTok AI Commenter")
    st.divider()
    st.subheader("Login to the TikTok Account that you want the bot to comment with.")

    if st.button("Login"):
        with st.spinner("waiting for completion..."):
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            title=loop.run_until_complete(save_session_to_json("https://www.tiktok.com/en/"))

    st.divider()
    st.subheader("Proxy Settings")

    proxy = st.radio("Use Proxy", ["Yes", "No"])

    if proxy == "Yes":
        proxy_server = st.text_input("Proxy Server")
        proxy_port = st.text_input("Proxy Port")
        proxy_username = st.text_input("Proxy Username")
        proxy_password = st.text_input("Proxy Password")
    elif proxy == "No":
        proxy_server = None
        proxy_port = None
        proxy_username = None
        proxy_password = None

    st.divider()
    st.subheader("Add Creators to the List")
    creator_count = st.number_input("How many creator do you want to add to the list", min_value=0, step=1)

    creator_names_list = []

    for i in range(creator_count):
        creator_name = st.text_input(f"Enter Creator Name {i+1}.", placeholder="username", key=f'creator_name{i}')
        creator_names_list.append(creator_name)

    if st.button("Save Creators to List"):
        with open ("assets/creators list.txt", 'a') as file:
            for i in range(len(creator_names_list)):
                file.write(f'{creator_names_list[i]}\n')
        st.success("Creators List Saved")

    st.subheader("OR Import a Creators List file")
    st.warning("The File must be a .txt and there should only be 1 creator name in each line")
    file_select = st.file_uploader("Select Creators List")

    if file_select:
        current_folder_path = os.getcwd()
        current_folder_path = os.path.join(current_folder_path, 'assets')
        dest_file_path = os.path.join(current_folder_path, 'creators list.txt')
        with open(dest_file_path, 'wb') as f:
            f.write(file_select.read())
        st.success("Creators List Has been Imported Successfully.")

    if st.button("Show Creators List"):
        try:
            with open ("assets/creators list.txt", 'r') as file:
                    show_creators = file.read().splitlines()
            for i in range(len(show_creators)):
                st.info(f"{i+1}. {show_creators[i]}")
        except:
            st.info("The Creators list is empty.")

    if st.button("Clear Creators List", type="primary"):
        try:
            with open ("assets/creators list.txt", 'w') as file:
                file.write()
        except:
            pass
        st.success("Creators List was Cleared")

    st.divider()
    prompt = st.text_area("Enter Prompt")

    st.subheader("Start the Process")
    if st.button("Start Commenting"):
        with st.spinner("Running..."):
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
            try:
                title=loop.run_until_complete(main(proxy_server, proxy_port, proxy_username, proxy_password, proxy, prompt))
            except Exception as e:
                print(e)
                st.error("Proxy Error, Change Proxy or Try Again.")
    