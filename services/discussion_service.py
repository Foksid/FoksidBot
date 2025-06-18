# services/discussion_service.py

pending_comments = {}

def store_pending_first_comment(channel_id, channel_message_id, comment_text, comment_markup=None):
    pending_comments[(channel_id, channel_message_id)] = {
        "text": comment_text,
        "markup": comment_markup
    }
