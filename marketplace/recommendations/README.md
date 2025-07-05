
# Recommendation System Documentation

## Architecture Overview
![Recommendation System Architecture](recommendation_architecture.png)

## API Endpoints
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/recommendations/<user_id>/` | GET | Get personalized recommendations |
| `/recommendations/similar/<listing_id>/` | GET | Find similar listings |

## Data Flow
1. User interactions tracked via signals
2. Behavior stored in Redis sorted sets
3. Periodic model training (daily)
4. Recommendations served via API

## Configuration
```python
# settings.py
RECOMMENDATION_SETTINGS = {
    'MIN_INTERACTIONS': 3,
    'REDIS_TTL': 86400,  # 1 day
    'MODEL_PATH': 'recommendations/models/'
}
```

## Testing
Run tests with:
```bash
python manage.py test marketplace.recommendations
```

## Monitoring
Key metrics to track:
- Recommendation click-through rate
- Model accuracy
- API response times
