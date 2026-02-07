# app.py - Ücretsiz Domino Shorts Web Uygulaması
# Flask ile telefondan erişilebilir sistem

from flask import Flask, render_template, request, jsonify, send_file
from gtts import gTTS
import requests
import os
import random
import uuid
from datetime import datetime
import threading
import json

app = Flask(__name__)

# Ayarlar
OUTPUT_DIR = "output"
TEMP_DIR = "temp"
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Aktif üretim durumları
active_jobs = {}

# Domino senaryoları
SCENARIOS = [
    {
        "title": "🌈 Renkli Domino Şelalesi",
        "text": "Muhteşem bir domino gösterisi başlıyor! Renkli taşlarımız kırmızıdan mora sırayla dizilmiş. İlk taş devrildi ve zincirleme reaksiyon başladı!",
        "query": "colorful domino falling"
    },
    {
        "title": "🔥 Ateş ve Buz Dominosu",
        "text": "Bu sefer inanılmaz bir domino yolculuğu yapıyoruz! Kırmızı ve mavi taşlar birbirini takip ediyor. Ne kadar heyecan verici değil mi?",
        "query": "domino chain reaction"
    },
    {
        "title": "🌟 Galaksi Domino Yolu",
        "text": "Uzayda bir domino gösterisi! Parlayan taşlarımız yıldızlar gibi parlıyor. Bakalım hepsi düzgün devrilecek mi?",
        "query": "domino spiral colorful"
    },
    {
        "title": "🎨 Sanat Eseri Dominosu",
        "text": "Domino taşlarıyla muhteşem bir sanat eseri yaratıyoruz! Her taş bir renk, her renk bir hikaye. İşte başlıyor!",
        "query": "domino art pattern"
    },
    {
        "title": "🏰 Kale İnşaatı Dominosu",
        "text": "Domino taşlarıyla dev bir kale inşa ediyoruz! Taş taş üstüne, kat kat yükseliyor. Sonunda ne olacak acaba?",
        "query": "domino tower building"
    },
    {
        "title": "🌊 Okyanus Dalgası Dominosu",
        "text": "Mavi domino taşları dalga gibi hareket ediyor! Bir dalga geldi, diğeri gidiyor. Ne güzel bir manzara!",
        "query": "blue domino wave"
    },
    {
        "title": "🚀 Uzay Yolculuğu Dominosu",
        "text": "Roket gibi hızlı domino taşları! Uzaya doğru fırlıyorlar. Hazır mısınız bu yolculuğa?",
        "query": "domino speed fast"
    },
    {
        "title": "🎪 Sirk Gösterisi Dominosu",
        "text": "Sirkte domino gösterisi var! Akrobatik hareketlerle devriliyorlar. Alkışlar lütfen!",
        "query": "domino trick amazing"
    },
    {
        "title": "🏔️ Dağ Tırmanışı Dominosu",
        "text": "Domino taşları dağa tırmanıyor! Yukarı yukarı çıkıyorlar. Zirveye ulaşabilecekler mi?",
        "query": "domino stairs climbing"
    },
    {
        "title": "🎆 Havai Fişek Dominosu",
        "text": "Patlayan renkler, uçuşan domino taşları! Havai fişek gibi gökyüzünü aydınlatıyorlar. Ne muhteşem!",
        "query": "colorful domino explosion"
    }
]

def download_stock_video(query, output_path):
    """Pexels'ten ücretsiz video indir"""
    try:
        # Pexels API (ücretsiz, sınırsız)
        api_key = "563492ad6f91700001000001c4c0ef8e6dc44d95a85491c560e35d66"
        url = f"https://api.pexels.com/videos/search?query={query}&per_page=20&orientation=portrait"
        
        headers = {"Authorization": api_key}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            videos = response.json().get('videos', [])
            if videos:
                # Rastgele video seç
                video = random.choice(videos)
                
                # 9:16 veya dikey videoyu bul
                video_file = None
                for vf in video['video_files']:
                    if vf.get('width', 0) <= vf.get('height', 0):  # Dikey video
                        video_file = vf
                        break
                
                if not video_file:
                    video_file = video['video_files'][0]  # En az ilk videoyu al
                
                video_url = video_file['link']
                
                # İndir
                video_data = requests.get(video_url, timeout=30)
                with open(output_path, 'wb') as f:
                    f.write(video_data.content)
                
                return True
    except Exception as e:
        print(f"Video indirme hatası: {e}")
    
    return False

def generate_voice(text, output_path):
    """Google TTS ile Türkçe ses"""
    try:
        tts = gTTS(text=text, lang='tr', slow=False)
        tts.save(output_path)
        return True
    except Exception as e:
        print(f"Ses üretim hatası: {e}")
        return False

def create_simple_video(video_path, audio_path, output_path):
    """FFmpeg olmadan basit video + ses birleştirme"""
    try:
        # MoviePy kullan (FFmpeg içerir)
        from moviepy.editor import VideoFileClip, AudioFileClip
        
        video = VideoFileClip(video_path)
        audio = AudioFileClip(audio_path)
        
        # Video boyutunu ayarla (9:16)
        if video.w > video.h:  # Yatay video
            video = video.resize(height=1920)
            video = video.crop(x_center=video.w/2, width=1080, height=1920)
        else:  # Dikey video
            video = video.resize(height=1920)
            if video.w < 1080:
                video = video.resize(width=1080)
            video = video.crop(x_center=video.w/2, width=1080, height=1920)
        
        # Süreyi ses uzunluğuna göre ayarla
        duration = min(video.duration, audio.duration, 60)  # Max 60 saniye
        
        video = video.subclip(0, duration)
        audio = audio.subclip(0, duration)
        
        # Ses ekle
        final = video.set_audio(audio)
        
        # Kaydet
        final.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',  # Hızlı render
            threads=4,
            logger=None  # Sessiz mod
        )
        
        video.close()
        audio.close()
        
        return True
        
    except Exception as e:
        print(f"Video oluşturma hatası: {e}")
        return False

def generate_videos_background(job_id, video_count):
    """Arka planda video üretimi"""
    job = active_jobs[job_id]
    
    try:
        for i in range(1, video_count + 1):
            # Durum güncelle
            job['current_video'] = i
            job['status'] = 'processing'
            job['message'] = f'Video {i}/{video_count} üretiliyor...'
            
            # Rastgele senaryo seç
            scenario = random.choice(SCENARIOS)
            
            job['current_stage'] = f"Senaryo: {scenario['title']}"
            
            # Video indir
            video_path = os.path.join(TEMP_DIR, f"{job_id}_video_{i}.mp4")
            job['current_stage'] = 'Domino videosu indiriliyor...'
            
            if not download_stock_video(scenario['query'], video_path):
                job['current_stage'] = 'Video bulunamadı, bir sonraki denenecek...'
                continue
            
            # Ses oluştur
            audio_path = os.path.join(TEMP_DIR, f"{job_id}_audio_{i}.mp3")
            job['current_stage'] = 'Türkçe seslendirme ekleniyor...'
            
            if not generate_voice(scenario['text'], audio_path):
                continue
            
            # Video + ses birleştir
            output_path = os.path.join(OUTPUT_DIR, f"{job_id}_domino_{i}.mp4")
            job['current_stage'] = 'Video montajlanıyor...'
            
            if create_simple_video(video_path, audio_path, output_path):
                job['completed_videos'].append({
                    'id': i,
                    'title': scenario['title'],
                    'filename': f"{job_id}_domino_{i}.mp4",
                    'path': output_path
                })
            
            # İlerleme güncelle
            job['progress'] = int((i / video_count) * 100)
            
            # Geçici dosyaları temizle
            try:
                os.remove(video_path)
                os.remove(audio_path)
            except:
                pass
        
        # Tamamlandı
        job['status'] = 'completed'
        job['message'] = f"{len(job['completed_videos'])} video hazır!"
        job['progress'] = 100
        
    except Exception as e:
        job['status'] = 'error'
        job['message'] = f'Hata: {str(e)}'
        print(f"İş hatası: {e}")

@app.route('/')
def index():
    """Ana sayfa"""
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate():
    """Video üretimini başlat"""
    data = request.json
    video_count = int(data.get('videoCount', 3))
    
    # İş oluştur
    job_id = str(uuid.uuid4())[:8]
    active_jobs[job_id] = {
        'id': job_id,
        'status': 'starting',
        'progress': 0,
        'current_video': 0,
        'total_videos': video_count,
        'completed_videos': [],
        'message': 'Hazırlanıyor...',
        'current_stage': '',
        'created_at': datetime.now().isoformat()
    }
    
    # Arka planda başlat
    thread = threading.Thread(
        target=generate_videos_background,
        args=(job_id, video_count)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'jobId': job_id,
        'message': f'{video_count} video üretimi başlatıldı'
    })

@app.route('/status/<job_id>')
def status(job_id):
    """İş durumunu sorgula"""
    job = active_jobs.get(job_id)
    
    if not job:
        return jsonify({
            'success': False,
            'error': 'İş bulunamadı'
        }), 404
    
    return jsonify({
        'success': True,
        'job': job
    })

@app.route('/download/<job_id>/<filename>')
def download(job_id, filename):
    """Video indir"""
    file_path = os.path.join(OUTPUT_DIR, filename)
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name=filename
        )
    
    return jsonify({
        'success': False,
        'error': 'Dosya bulunamadı'
    }), 404

if __name__ == '__main__':
    # Ücretsiz hosting için 0.0.0.0
    app.run(host='0.0.0.0', port=5000, debug=True)
