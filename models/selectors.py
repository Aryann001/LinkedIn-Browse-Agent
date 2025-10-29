from beanie import Document
from pydantic import Field

class SelectorConfig(Document):
    # We use our last-known-good selectors as the defaults.
    # This way, the app works "out of the box" and only
    # uses new selectors if they are saved in the database.
    
    post_container: str = Field(default="div.feed-shared-update-v2")
    
    author_selector: str = Field(
        default=".update-components-actor__single-line-truncate span[aria-hidden='true']"
    )
    content_selector: str = Field(
        default=".update-components-update-v2__commentary"
    )
    like_button: str = Field(default="button.react-button__trigger")
    comment_button: str = Field(default="button.comment-button")
    comment_textbox: str = Field(default="div.ql-editor[contenteditable='true']")
    comment_post_button: str = Field(
        default="button.comments-comment-box__submit-button--cr"
    )

    class Settings:
        name = "selector_config"