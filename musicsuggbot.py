from spotipy.oauth2 import SpotifyClientCredentials
import spotipy
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from collections import Counter

# Spotify API credentials
SPOTIFY_CLIENT_ID = "a712aee246a04324b971b935d368d8aa"
SPOTIFY_CLIENT_SECRET = "54bfb09cb57a411bb3f0c6cd3d8f7e0e"

# Telegram Bot Token
TOKEN = "7778448900:AAF0OaVMauyMkSzCj99Z13ZlTNy-Z13v4ks"

# Spotify API authentication
auth_manager = SpotifyClientCredentials(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
spotify = spotipy.Spotify(auth_manager=auth_manager)

# Получение жанров из плейлиста
def get_genres_from_playlist(playlist_id):
    try:
        results = spotify.playlist_tracks(playlist_id)
        tracks = results['items']
        genre_map = {}
        for track in tracks:
            artists = track['track']['artists']
            for artist in artists:
                artist_id = artist['id']
                artist_name = artist['name']
                artist_info = spotify.artist(artist_id)
                genres = artist_info.get('genres', [])
                genre_map[artist_name] = genres
        return genre_map
    except Exception as e:
        print(f"Ошибка: {e}")
        return {}

# Получение популярных жанров
def get_popular_genres(genre_data):
    genre_counter = Counter()
    for genres in genre_data.values():
        genre_counter.update(genres)

    popular_genres = genre_counter.most_common(5)
    return popular_genres

# Поиск малоизвестных исполнителей по жанру
def find_unknown_artists(genre, max_listeners=50000):
    try:
        print(f"Ищу артистов для жанра: {genre}")
        results = spotify.search(q=f"genre:{genre}", type="artist", limit=50)
        artists = results['artists']['items']
        print(f"Найдено {len(artists)} артистов для жанра {genre}")

        unknown_artists = [
            {
                "name": artist["name"],
                "listeners": artist["followers"]["total"],
                "link": artist["external_urls"]["spotify"]
            }
            for artist in artists if artist["followers"]["total"] <= max_listeners
        ]

        return unknown_artists

    except Exception as e:
        print(f"Ошибка при поиске артистов для жанра {genre}: {e}")
        return []

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for /start command."""
    await update.message.reply_text(
        "Привет! Отправь мне ссылку на плейлист Spotify, и я найду жанры его треков, а также предложу малоизвестных исполнителей! 🎵"
    )

# Обработка плейлистов
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler for receiving playlist links."""
    message = update.message.text

    if "spotify.com/playlist/" in message:
        try:
            playlist_id = message.split("playlist/")[1].split("?")[0]
            genre_data = get_genres_from_playlist(playlist_id)
            if genre_data:
                popular_genres = get_popular_genres(genre_data)
                response = "Вот рекомендации по малоизвестным артистам:\n\n"
                any_artists_found = False  # Проверка, найдены ли артисты

                for genre, _ in popular_genres:
                    artists = find_unknown_artists(genre)
                    if artists:  # Добавляем жанр только если найдены артисты
                        response += f"🎵 Жанр: {genre}\n"
                        for artist in artists:
                            response += f"  - [{artist['name']}]({artist['link']}) ({artist['listeners']} слушателей)\n"
                        response += "\n"
                        any_artists_found = True

                if not any_artists_found:  # Если ни для одного жанра не найдено артистов
                    response = "Не удалось найти малоизвестных исполнителей для предложенных жанров."
            else:
                response = "Не удалось получить данные о жанрах. Возможно, плейлист пуст или доступ к нему ограничен."
        except Exception as e:
            response = f"Произошла ошибка при обработке плейлиста: {e}"
    else:
        response = "Пожалуйста, отправь мне корректную ссылку на плейлист Spotify."

    await update.message.reply_text(response, parse_mode="Markdown")

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    print("Бот запущен...")
    app.run_polling()
