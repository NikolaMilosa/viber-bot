from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
import requests
import json
import os
from viberbot.api.messages import (
    TextMessage
)
import logging
from datetime import datetime

def get_logger():
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger

def configure_bot(url):
    auth_token = os.environ.get("VIBER_BOT_KEY")
    bot_config = BotConfiguration(
        name="SotexBarman",
        auth_token=auth_token,
        avatar="https://dl-media.viber.com/1/share/2/long/vibes/icon/image/0x0/3e5d/21be6c0328b1b1bba8d806b9f4626958a036abd03a6276e1c33b6db0b37c3e5d.jpg"
    )

    viber = Api(bot_config)
    viber.set_webhook(url)
    
    return viber

def get_accounts(url):
    response = requests.get(url).json()
    print(response)
    return response['subscribers']

def get_feed(email, password):
    headers = {
        "Accept": "application/json",
    }
    response = requests.get('https://sso.daily.dev/self-service/login/browser', headers=headers)
    cookies = response.cookies
    response = response.json()
    uri = response['ui']['action']
    csrf_token = [x for x in response['ui']['nodes'] if x['group'] == 'default' and x['attributes']['name'] == "csrf_token"][0]['attributes']['value']
    
    body = {
        "identifier": email,
        "password": password,
        "method": "password",
        "csrf_token": csrf_token
    }
    response = requests.post(uri, body, headers=headers, cookies=cookies)
    cookies.update(response.cookies)
    
    response = requests.get('https://api.daily.dev/boot', headers=headers, cookies=cookies)
    cookies.update(response.cookies)

    topics = {
        "cloud": {
            "tags": ["azure", "cloud"],
            "topics": []
        },
        "databases": {
            "tags": ["mssql", "sql"],
            "topics": []
        },
        "fundamentals": {
            "tags": ["dependency-injection", "design-patterns", "microservices"],
            "topics": []
        },
        "dotnet": {
            "tags": [".net", "c#", ".net-core"],
            "topics": []
        }
    }
    after = ''
    while True:
        data = {
            "query": "\n  query Feed(\n    $loggedIn: Boolean! = false\n    $first: Int\n    $after: String\n    $ranking: Ranking\n    $version: Int\n    $supportedTypes: [String!] = [\"article\",\"share\",\"freeform\"]\n  ) {\n    page: feed(\n      first: $first\n      after: $after\n      ranking: $ranking\n      version: $version\n      supportedTypes: $supportedTypes\n    ) {\n      ...FeedPostConnection\n    }\n  }\n  \n  fragment FeedPostConnection on PostConnection {\n    pageInfo {\n      hasNextPage\n      endCursor\n    }\n    edges {\n      node {\n        ...FeedPost\n        contentHtml\n        ...UserPost @include(if: $loggedIn)\n      }\n    }\n  }\n  \n  fragment FeedPost on Post {\n    ...SharedPostInfo\n    sharedPost {\n      ...SharedPostInfo\n    }\n    trending\n    feedMeta\n  }\n  \n  fragment SharedPostInfo on Post {\n    id\n    title\n    titleHtml\n    image\n    readTime\n    permalink\n    commentsPermalink\n    summary\n    createdAt\n    private\n    upvoted\n    commented\n    bookmarked\n    views\n    numUpvotes\n    numComments\n    scout {\n      ...UserShortInfo\n    }\n    author {\n      ...UserShortInfo\n    }\n    type\n    tags\n    source {\n      ...SourceBaseInfo\n    }\n    downvoted\n    flags {\n      promoteToPublic\n    }\n    userState {\n      vote\n      flags {\n        feedbackDismiss\n      }\n    }\n  }\n  \n  fragment SourceBaseInfo on Source {\n    id\n    active\n    handle\n    name\n    permalink\n    public\n    type\n    description\n    image\n    membersCount\n    privilegedMembers {\n      user {\n        id\n      }\n      role\n    }\n    currentMember {\n      ...CurrentMember\n    }\n    memberPostingRole\n    memberInviteRole\n  }\n  \n  fragment CurrentMember on SourceMember {\n    user {\n      id\n    }\n    permissions\n    role\n    referralToken\n    flags {\n      hideFeedPosts\n      collapsePinnedPosts\n    }\n  }\n\n\n  \n  fragment UserShortInfo on User {\n    id\n    name\n    image\n    permalink\n    username\n    bio\n  }\n\n\n\n  \n  fragment UserPost on Post {\n    read\n    upvoted\n    commented\n    bookmarked\n    downvoted\n  }\n\n\n",
            "variables": {
                "version": 17,
                "ranking": "TIME",
                "first": 50,
                "loggedIn": True,
                "after": after
            }
        }

        page = requests.post('https://api.daily.dev/graphql', json=data, headers=headers, cookies=cookies).json()['data']['page']
        after = page['pageInfo']['endCursor']

        # title = edge['title']
        # link = edge['permalink']
        # created_at = edge['createdAt']

        for key in topics:
            current_topic = topics[key]

            if len(current_topic['topics']) >= 3:
                continue

            relevant = [link['node'] for link in page['edges'] if any([tag in current_topic['tags'] for tag in link['node']['tags']])]

            current_topic['topics'] += [{
                "title": edge['title'],
                "link": edge['permalink'],
                "created_at": edge['createdAt']
            } for edge in relevant]

        if all([len(topics[topic]['topics']) >= 3 for topic in topics]):
            break
    
    now = datetime.now()
    format_string = "%Y-%m-%dT%H:%M:%S.%fZ"
    start_of_day = datetime(now.year, now.month, now.day, 0, 0, 0, 0)

    for topic in topics:
        current_topic = topics[topic]
        current_topic["topics"] = sorted(current_topic["topics"], key=lambda x: datetime.strptime(x['created_at'], format_string))[0:2]
        current_topic["topics"] = [post for post in current_topic["topics"] if datetime.strptime(post['created_at'], format_string) < start_of_day]

    return topics

def format_message(topics): 
    message_test = "Pozdrav! Evo zanimljivih linkova za današnji dan:"
    for topic in topics:
        message_test += f"\n\n{topic.capitalize()}:"
        for blog in topics[topic]['topics']:
            message_test += f"\n{blog['title']}: {blog['link']}"

    return message_test

def main():
    get_logger()

    email = os.environ.get('EMAIL')
    password = os.environ.get('PASS')
    url = os.environ.get("URL")
    viber = configure_bot(url)

    message = format_message(get_feed(email, password))

    for member in get_accounts(url):
        viber.send_messages(to=member['id'],
			     messages=[TextMessage(text=message)])

if __name__ == "__main__":
    main()



