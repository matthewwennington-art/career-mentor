import streamlit_authenticator as stauth

# 1. Type the password you want to give your guest here
password_to_hash = 'InviteOnly2026' 

# 2. This creates the secure, scrambled version
hashed_password = stauth.Hasher.hash(password_to_hash)

print(f"\n--- COPY THE STRING BELOW ---")
print(hashed_password)
print(f"--- END OF HASH ---\n")
