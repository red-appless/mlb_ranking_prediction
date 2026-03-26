import requests
import json
import datetime

# 1. チーム名とIDのマッピング
TEAM_ID = {
    "ブルージェイズ": 141, "オリオールズ": 110, "ヤンキース": 147, "レッドソックス": 111, "レイズ": 139,
    "タイガース": 116, "ロイヤルズ": 118, "ガーディアンズ": 114, "ツインズ": 142, "ホワイトソックス": 145,
    "マリナーズ": 136, "アストロズ": 117, "レンジャース": 140, "アスレチックス": 133, "エンゼルス": 108,
    "メッツ": 121, "フィリーズ": 143, "ブレーブス": 144, "マーリンズ": 146, "ナショナルズ": 120,
    "ブリュワーズ": 158, "カブス": 112, "パイレーツ": 134, "レッズ": 113, "カージナルス": 138,
    "ドジャース": 119, "ジャイアンツ": 137, "ダイアモンドバックス": 109, "パドレス": 135, "ロッキーズ": 115
}
ID_TO_NAME = {v: k for k, v in TEAM_ID.items()}

# 2. 地区IDと名前の対応
DIVISION_MAP = {
    201: "American League East",
    202: "American League Central",
    200: "American League West",
    204: "National League East",
    205: "National League Central",
    203: "National League West"
}

# 3. 予想データ
PREDICTIONS = {
    "井口健介": {
        "American League East": [111, 141, 147, 110, 139],
        "American League Central": [116, 118, 114, 142, 145],
        "American League West": [136, 117, 140, 133, 108],
        "National League East": [121, 143, 144, 146, 120],
        "National League Central": [158, 112, 134, 113, 138],
        "National League West": [119, 137, 109, 135, 115]
    },
    "細川峻平": {
        "American League East": [141, 110, 147, 111, 139],
        "American League Central": [116, 114, 145, 118, 142],
        "American League West": [117, 136, 140, 133, 108],
        "National League East": [143, 121, 144, 120, 146],
        "National League Central": [112, 158, 113, 134, 138],
        "National League West": [137, 119, 135, 109, 115]
    },
    "田中雄太郎": {
        "American League East": [141, 111, 147, 139, 110],
        "American League Central": [114, 116, 118, 145, 142],
        "American League West": [136, 133, 117, 140, 108],
        "National League East": [121, 143, 144, 146, 120],
        "National League Central": [112, 158, 138, 113, 134],
        "National League West": [119, 135, 109, 137, 115]
    }
}

def count_inversions(actual, prediction):
    rank_map = {team_id: i for i, team_id in enumerate(actual)}
    prediction_ranks = [rank_map[tid] for tid in prediction if tid in rank_map]
    inversions = 0
    for i in range(len(prediction_ranks)):
        for j in range(i + 1, len(prediction_ranks)):
            if prediction_ranks[i] > prediction_ranks[j]:
                inversions += 1
    return inversions

def main():
    year = 2026
    url = f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={year}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        mlb_data = response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    results = {
        "last_updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST"),
        "scores": {user: 0 for user in PREDICTIONS.keys()},
        "divisions": []
    }

    if "records" not in mlb_data:
        return

    for record in mlb_data["records"]:
        div_id = record.get("division", {}).get("id")
        if div_id not in DIVISION_MAP:
            continue
        
        division_name = DIVISION_MAP[div_id]
        team_records = record.get("teamRecords", [])
        actual_standings = [team["team"]["id"] for team in team_records]
        
        if not actual_standings:
            continue

        division_entry = {"name": division_name, "teams": []}

        # スコア計算
        for user in PREDICTIONS.keys():
            user_pred = PREDICTIONS[user].get(division_name, [])
            results["scores"][user] += count_inversions(actual_standings, user_pred)

        # チーム詳細データ（成績データ追加）
        for i, team_record in enumerate(team_records):
            team_id = team_record["team"]["id"]
            team_info = {
                "id": team_id,
                "name": ID_TO_NAME.get(team_id, f"Unknown({team_id})"),
                "actual_rank": i + 1,
                "wins": team_record.get("wins", 0),
                "losses": team_record.get("losses", 0),
                "pct": float(team_record.get("winningPercentage", 0)),
                "predictions": {user: PREDICTIONS[user][division_name].index(team_id) + 1 
                               for user in PREDICTIONS if team_id in PREDICTIONS[user].get(division_name, [])}
            }
            division_entry["teams"].append(team_info)
        
        results["divisions"].append(division_entry)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully updated. Divisions found: {len(results['divisions'])}")

if __name__ == "__main__":
    main()
    