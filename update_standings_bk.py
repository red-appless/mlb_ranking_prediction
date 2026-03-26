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

# 2. 地区と所属チームIDの定義
DIVISION_STRUCTURE = {
    "American League East": [141, 110, 147, 111, 139],
    "American League Central": [116, 118, 114, 142, 145],
    "American League West": [136, 117, 140, 133, 108],
    "National League East": [121, 143, 144, 146, 120],
    "National League Central": [158, 112, 134, 113, 138],
    "National League West": [119, 137, 109, 135, 115]
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
    url = f"https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season={year}&standingsType=springTraining"
    
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

    # 全チームの最新スタッツを抽出
    all_teams_stats = {}
    for record in mlb_data.get("records", []):
        for team_record in record.get("teamRecords", []):
            tid = team_record["team"]["id"]
            all_teams_stats[tid] = {
                "pct": float(team_record.get("winningPercentage", 0)),
                "wins": team_record.get("wins", 0),
                "losses": team_record.get("losses", 0)
            }

    # 地区ごとに集計
    for div_name, div_team_ids in DIVISION_STRUCTURE.items():
        # 勝率の高い順にソート（地区内順位）
        sorted_in_div = sorted(
            div_team_ids, 
            key=lambda tid: all_teams_stats.get(tid, {}).get("pct", 0), 
            reverse=True
        )
        
        division_entry = {"name": div_name, "teams": []}

        # スコア計算
        for user in PREDICTIONS.keys():
            user_pred = PREDICTIONS[user].get(div_name, [])
            results["scores"][user] += count_inversions(sorted_in_div, user_pred)

        # チーム詳細データ（W, L, PCTを含む）
        for i, team_id in enumerate(sorted_in_div):
            stats = all_teams_stats.get(team_id, {"wins": 0, "losses": 0, "pct": 0})
            team_info = {
                "id": team_id,
                "name": ID_TO_NAME.get(team_id, f"Unknown({team_id})"),
                "actual_rank": i + 1,
                "wins": stats["wins"],
                "losses": stats["losses"],
                "pct": stats["pct"],
                "predictions": {user: PREDICTIONS[user][div_name].index(team_id) + 1 
                               for user in PREDICTIONS if team_id in PREDICTIONS[user].get(div_name, [])}
            }
            division_entry["teams"].append(team_info)
        
        results["divisions"].append(division_entry)

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"Spring Training data updated. Divisions: {len(results['divisions'])}")

if __name__ == "__main__":
    main()
