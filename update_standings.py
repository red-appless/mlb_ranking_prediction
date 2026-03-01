import requests
import json
import datetime

# チーム名とIDのマッピング
TEAM_ID = {
    "ブルージェイズ": 147, "オリオールズ": 110, "ヤンキース": 111, "レッドソックス": 141, "レイズ": 139,
    "タイガース": 116, "ロイヤルズ": 118, "ガーディアンズ": 114, "ツインズ": 142, "ホワイトソックス": 145,
    "マリナーズ": 136, "アストロズ": 117, "レンジャース": 140, "アスレチックス": 133, "エンゼルス": 108, "エンジェルス": 108,
    "メッツ": 121, "フィリーズ": 143, "ブレーブス": 144, "マーリンズ": 146, "ナショナルズ": 120,
    "ブリュワーズ": 158, "カブス": 112, "パイレーツ": 134, "レッズ": 113, "カージナルス": 138,
    "ドジャース": 119, "ジャイアンツ": 137, "ダイアモンドバックス": 109, "パドレス": 135, "ロッキーズ": 115
}

ID_TO_NAME = {v: k for k, v in TEAM_ID.items()}

# 3人の予想データ
PREDICTIONS = {
    "井口健介": {
        "American League East": [141, 147, 111, 110, 139],
        "American League Central": [116, 118, 114, 142, 145],
        "American League West": [136, 117, 140, 133, 108],
        "National League East": [121, 143, 144, 146, 120],
        "National League Central": [158, 112, 134, 113, 138],
        "National League West": [119, 137, 109, 135, 115]
    },
    "細川峻平": {
        "American League East": [147, 110, 111, 141, 139],
        "American League Central": [116, 114, 145, 118, 142],
        "American League West": [117, 136, 140, 133, 108],
        "National League East": [143, 121, 144, 120, 146],
        "National League Central": [112, 158, 113, 134, 138],
        "National League West": [137, 119, 135, 109, 115]
    },
    "田中雄太郎": {
        "American League East": [147, 141, 111, 139, 110],
        "American League Central": [114, 116, 118, 145, 142],
        "American League West": [136, 133, 117, 140, 108],
        "National League East": [121, 143, 144, 146, 120],
        "National League Central": [112, 158, 138, 113, 134],
        "National League West": [119, 135, 109, 137, 115]
    }
}

def count_inversions(actual, prediction):
    n = len(actual)
    if n != len(prediction): return 0
    rank_map = {team_id: i for i, team_id in enumerate(actual)}
    try:
        prediction_ranks = [rank_map[team_id] for team_id in prediction]
    except KeyError: return 0
    inversions = 0
    for i in range(n):
        for j in range(i + 1, n):
            if prediction_ranks[i] > prediction_ranks[j]: inversions += 1
    return inversions

def main():
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
    try:
        response = requests.get(url)
        response.raise_for_status()
        mlb_data = response.json()
    except Exception as e:
        print(f"Error: {e}"); return

    results = {
        "last_updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST"),
        "scores": {user: 0 for user in PREDICTIONS.keys()},
        "divisions": []
    }

    target_divisions = [
        "American League East", "American League Central", "American League West",
        "National League East", "National League Central", "National League West"
    ]

    for record in mlb_data.get("records", []):
        division_name = record["division"]["name"]
        if division_name not in target_divisions: continue

        actual_standings = [team["team"]["id"] for team in record["teamRecords"]]
        division_data = {"name": division_name, "teams": []}

        for user, div_preds in PREDICTIONS.items():
            results["scores"][user] += count_inversions(actual_standings, div_preds.get(division_name, []))

        for i, team_id in enumerate(actual_standings):
            team_info = {"id": team_id, "name": ID_TO_NAME.get(team_id, f"ID:{team_id}"), "actual_rank": i + 1, "predictions": {}}
            for user, div_preds in PREDICTIONS.items():
                user_pred = div_preds.get(division_name, [])
                try: team_info["predictions"][user] = user_pred.index(team_id) + 1
                except ValueError: team_info["predictions"][user] = "-"
            division_data["teams"].append(team_info)
        results["divisions"].append(division_data)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()