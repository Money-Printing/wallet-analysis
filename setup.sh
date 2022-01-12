mkdir -p ~/.streamlit/
printf "\
[general]\n\
email = \"ankurdwivedi75@gmail.com\"\n\
" > ~/.streamlit/credentials.toml
printf "\
[server]\n\
headless = true\n\
enableCORS = false\n\
port = %s\n\
" "$PORT"> ~/.streamlit/config.toml