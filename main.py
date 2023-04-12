import argparse
import googleapiclient.discovery

from googleapiclient.discovery import build

DEVELOPER_KEY = "RLY?"

def get_channel_playlists(channel_id_or_username):
	# Set up the YouTube Data API client
	api_service_name = "youtube"
	api_version = "v3"
	client = build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

	# Set up the parameters for the playlist search
	if channel_id_or_username.startswith("UC"):
		# The input is a channel ID
		channel_id = channel_id_or_username
		part = "contentDetails"
		request = client.channels().list(
			part=part,
			id=channel_id
		)
	else:
		# The input is a username
		username = channel_id_or_username
		part = "contentDetails"
		request = client.channels().list(
			part=part,
			forUsername=username
		)

	# Execute the request and get the list of playlists
	response = request.execute()

	# Print the response to the console for debugging
	print(response)

	channel = response.get("items", [])[0]
	playlists = channel["contentDetails"]["relatedPlaylists"]

	# Create a list of tuples with the playlist ID and title
	playlist_list = []
	for playlist_title, playlist_id in playlists.items():
		if playlist_id == "":
			# Skip this playlist if it doesn't have an ID
			continue
		print('Processing Playlist Title: ', playlist_title, 'Playlist ID: ', playlist_id)
		playlist_list.append((playlist_id, playlist_title))
		
	return playlist_list

def get_playlist_info(playlist_id, playlist_name):
	# Set up the YouTube Data API client
	api_service_name = "youtube"
	api_version = "v3"
	client = googleapiclient.discovery.build(
		api_service_name, api_version, developerKey=DEVELOPER_KEY)

	# Initialize the transcript string
	transcript = ""

	# Initialize the video titles list
	video_titles = []

	# Set up the parameters for the playlist items search
	playlist_items_request = client.playlistItems().list(
		playlistId=playlist_id,
		part="snippet"
	)
	# Execute the playlist items search and get the list of video IDs
	video_ids = []
	while playlist_items_request:
		print("Processing Playlist: ", playlist_id)
		playlist_items_response = playlist_items_request.execute()
		print("Playlist Items Response: ", playlist_items_response)
		for playlist_item in playlist_items_response['items']:
			video_id = playlist_item['snippet']['resourceId']['videoId']
			video_titles.append(playlist_item['snippet']['title'])
			video_ids.append(video_id)
		playlist_items_request = client.playlistItems().list_next(
			playlist_items_request, playlist_items_response)

	# For each video ID, get the transcript and add it to the transcript string
	for video_id in video_ids:
		transcript = get_video_transcript(video_id)
		if transcript:
			transcript_string += transcript + "\n"
		else:
			# Skip this video if no English transcript is available
			continue

	# Return the playlist name, the video titles, and the transcript string
	return (playlist_name, video_titles, transcript)

def get_video_transcript(video_id):
    # Set up the YouTube Data API client
    api_service_name = "youtube"
    api_version = "v3"
    client = build(api_service_name, api_version, developerKey=DEVELOPER_KEY)

    # Call the captions.list method to get the list of caption tracks for the video
    captions_request = client.captions().list(
        videoId=video_id,
		part="snippet"
        
    )
    captions_response = captions_request.execute()

    # Iterate through the list of caption tracks and find the one in English
    english_track = None
    for track in captions_response["items"]:
        if track["snippet"]["language"] == "en":
            english_track = track
            break

    # If an English caption track was found, return the transcript text
    if english_track:
        return english_track["snippet"]["textDisplay"]
    else:
        return None

def write_playlist_files(playlist_info):
	# Unpack the playlist information
	playlist_name, video_titles, transcript = playlist_info

	# Split the transcript into a list of transcripts for each video
	transcripts = transcript.strip().split("\n\n")

	# Write a Markdown file for each video
	for i in range(len(video_titles)):
		# Set the file name and title for the current video
		file_name = f"{playlist_name} - {video_titles[i]}.md"
		title = f"# {playlist_name}\n## {video_titles[i]}"

		# Write the Markdown file for the current video
		with open(file_name, "w") as f:
			f.write(title + "\n\n")
			f.write(transcripts[i])

def write_channel_playlist_files(channel_id_or_username):
	# Get the list of playlists for the channel
	playlists = get_channel_playlists(channel_id_or_username)

	# Write a Markdown file for each video in each playlist
	for playlist in playlists:
		playlist_id, playlist_name = playlist
		playlist_info = get_playlist_info(playlist_id, playlist_name)
		write_playlist_files(playlist_info)

def main():
	# Set up the argument parser
	parser = argparse.ArgumentParser()
	parser.add_argument("channel_id_or_username", help="The ID or username of the channel")
	args = parser.parse_args()

	# Get the channel ID or username from the command-line arguments
	channel_id_or_username = args.channel_id_or_username

	# Write a Markdown file for each video in each playlist of the channel
	write_channel_playlist_files(channel_id_or_username)

if __name__ == "__main__":
	main()
