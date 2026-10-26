import bleach

TAGS = frozenset(
    [
        "p",
        "br",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "strong",
        "em",
        "u",
        "s",
        "blockquote",
        "pre",
        "code",
        "ul",
        "ol",
        "li",
        "a",
        "img",
        "table",
        "thead",
        "tbody",
        "tr",
        "th",
        "td",
        "span",
        "sub",
        "sup",
        "hr",
    ]
)


def clean_html(value):
    return bleach.clean(
        value or "",
        tags=TAGS,
        attributes={
            "a": ["href", "title"],
            "img": ["src", "alt", "width", "height"],
            "li": ["data-list"],
            "*": ["class"],
        },
        protocols=["https", "http"],
        strip=True,
    )
