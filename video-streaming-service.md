# System Design: Unified Video Streaming Platform (VOD + Live)

## 1. Requirements

### Functional
- User signup/login
- Upload video (VOD)
- Transcoding (multi-resolution, chunked video)
- Search/discover content
- Watch/play videos (adaptive streaming)
- Sync watch history across devices
- Start/stop live stream
- Live chat, reactions during stream
- Replay live as VOD
- Subscription management

### Non-Functional
- High availability (≥ 99.99%)
- Low latency (<5s VOD, <3s Live)
- High throughput (1M concurrent users)
- Scalability (auto-scaling workers, ingestion)
- Durability (video chunks, metadata)
- Cost-effective delivery (CDN, compression)
- Security (auth, DRM, content access control)

### Capacity Estimation (example)

| Metric                    | Value                     |
|--------------------------|---------------------------|
| MAU                      | 10M                        |
| Peak concurrent viewers  | 1M                         |
| Daily video uploads      | 10K                        |
| Avg upload size (raw)    | 500MB                      |
| Avg transcoded size      | ~3x raw (all resolutions)  |
| CDN bandwidth (peak)     | 100–300 Gbps               |

---

## 2. Core Entities

| Entity        | Description                                         |
|---------------|-----------------------------------------------------|
| User          | id, email, name, subscription_plan                  |
| Video         | id, owner_id, title, description, upload_time       |
| VideoMetadata | duration, status, available_resolutions, manifest   |
| LiveStream    | id, streamer_id, ingest_url, status, start_time     |
| Segment       | resolution, start_time, URL, sequence               |
| WatchHistory  | user_id, video_id, last_position                    |
| ChatMessage   | stream_id, user_id, content, timestamp              |

---

## 3. API / System Interfaces

### Upload
```http
POST /videos
Body: { file, title, description }
Returns: { video_id }
```

### Transcode Status
```http
GET /videos/:id/status
Returns: { ready: true, resolutions: [1080p, 720p] }
```

### Playback
```http
GET /videos/:id/manifest
Returns: { url: /manifest/video_id.m3u8 }
```

### Start Live
```http
POST /live/start
Returns: { ingest_url, stream_key }
```

### Search
```http
GET /search?q=cat
Returns: [ { video_id, title, thumbnail_url } ]
```


## 4. Optional Data Flow

### Video Upload (VOD)
  - Client uploads file → stored in object storage (e.g., S3).
  - Upload service emits job to message queue.
  - Transcoding workers process via FFmpeg, save chunks in storage.
  - Manifest generated and saved.
  - Metadata saved to DB and indexed in ElasticSearch.
  - Playback retrieves manifest; segments streamed via CDN.

### Live Streaming
  - Streamer starts with RTMP ingest URL.
  - Ingest server receives feed.
  - Live transcoder creates real-time segments.
  - Segments pushed to CDN and stored.
  - Manifest updated; clients fetch stream.
  - Live session optionally stored as VOD.

## 5. High Level Design

## 6. Deep Dives (Explained)

### 6.1 Transcoding Pipeline
  - Upload triggers a message to queue.
  - Transcoder picks job, uses FFmpeg to convert to multiple resolutions.
  - Chunks are created for each resolution and stored.
  - Manifests (HLS/DASH) generated.
  - Retry and scaling handled via worker pools.

### 6.2 CDN + Chunking
  - CDN caches manifest and segments.
  - HLS: .m3u8 + .ts chunks; DASH: .mpd + .m4s chunks.
  - Adaptive Bitrate Streaming (ABR) adjusts quality per bandwidth.

### 6.3 Search & Indexing
  - ElasticSearch stores indexed video metadata.
  - Primary DB is source of truth; indexers sync data to Elastic.

### 6.4 Watch History & Resume Playback
  - Player sends progress every few seconds.
  - Stored in Redis and periodically flushed to DB.
    When resuming:
      - History service returns last_position.
      - Playback client fetches manifest.
      - Client calculates corresponding chunk (e.g., start_time in .m3u8).
      - Requests that chunk and continues playback.

### 6.6 Caching Strategy
  - CDN: Manifest and segment caching.
  - Redis: Auth tokens, watch history, hot metadata.
  - Reduces latency and backend load.

### 6.7 Real-Time Chat for Live Streaming (Twitch-style)
  - WebSocket or IRC protocol used to establish persistent client connection.
  - Chat Gateway Service handles client messaging and connection scaling.
  - Messages are pushed to a PubSub system (like Kafka) for fan-out.
  - Optional moderation layer checks for spam, banned words.
  - Messages broadcast in real-time to viewers of the same stream.
  - Persistence: Messages can be saved to DB for future replay.
  - Key features: slow mode, emotes, moderation, commands, tagging.

