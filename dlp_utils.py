VERIFIED_RECIPIENTS = ["ea16826@gmail.com", "uzairarshad113@gmail.com", "1"]
BLOCKED_SITES = ["chat.openai.com", "drive.google.com"]

def is_verified_recipient(email):
    return email in VERIFIED_RECIPIENTS

def is_blocked_upload(url):
    return any(site in url for site in BLOCKED_SITES)