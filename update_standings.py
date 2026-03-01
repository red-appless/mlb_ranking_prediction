import requests
import json
import datetime

# ==========================================
# 友達3人の予想順位 (地区ごとに、1位から順にチームIDを並べる)
# チームIDの確認方法：https://statsapi.mlb.com/api/v1/teams
# ==========================================
PREDICTIONS = {
    "User1": { # Aさん
        "AL East": [147, 110, 111, 139, 141], # TOR, BAL, NYY, TB, BOS
        # 他の地区も同様に追加...
    },
    "User2": { # Bさん
        "AL East": [111, 147, 110, 141, 139], # NYY, TOR, BAL, BOS, TB
    },
    "User3": { # Cさん
        "AL East": [110, 111, 147, 139, 141], # BAL, NYY, TOR, TB, BOS
    }
}

# チーム名マッピング (IDだと分かりにくいので)
TEAM_NAMES = {
    110: "BAL", 111: "NYY", 139: "TB", 141: "BOS", 147: "TOR",
    # 他のチームも追加...
}

# 反転数 (Inversion Count) の計算
def count_inversions(actual, prediction):
    n = len(actual)
    if n != len(prediction): return 0
    # 予想の順に、結果におけるそのチームの順位を並べた配列を作る
    rank_map = {team_id: i for i, team_id in enumerate(actual)}
    prediction_ranks = [rank_map[team_id] for team_id in prediction]
    
    inversions = 0
    for i in range(n):
        for j in range(i + 1, n):
            if prediction_ranks[i] > prediction_ranks[j]:
                inversions += 1
    return inversions

def main():
    # 1. MLB APIから現在の順位を取得
    url = "https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026"
    try:
        response = requests.get(url)
        response.raise_for_status()
        mlb_data = response.json()
    except Exception as e:
        print(f"Error fetching MLB data: {e}")
        return

    # 2. データを解析して整形
    results = {
        "last_updated": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).strftime("%Y-%m-%d %H:%M:%S JST"),
        "scores": {user: 0 for user in PREDICTIONS.keys()},
        "divisions": []
    }

    for record in mlb_data.get("records", []):
        division_name = record["division"]["name"]
        if division_name not in ["American League East"]: # 今回はAL Eastのみ例示
            continue

        actual_standings = [team["team"]["id"] for team in record["teamRecords"]]
        
        division_data = {
            "name": division_name,
            "teams": []
        }

        # 地区ごとの各チームのデータを整理
        for i, team_id in enumerate(actual_standings):
            team_data = {
                "id": team_id,
                "name": TEAM_NAMES.get(team_id, str(team_id)),
                "actual_rank": i + 1,
                "predictions": {},
                "inversions": {}
            }
            # 3人の予想順位と、その時点での反転数を取得 (実際は地区単位で計算)
            division_data["teams"].append(team_data)

        # 地区ごとの反転数を計算してユーザーの合計スコアに加算
        for user, predictions in PREDICTIONS.items():
            user_div_prediction = predictions.get(division_name, [])
            inversion_count = count_inversions(actual_standings, user_div_prediction)
            results["scores"][user] += inversion_count
            
            # 各チームデータに、この地区でのこのユーザーの予想順位を入れる (表示用)
            pred_map = {team_id: i + 1 for i, team_id in enumerate(user_div_prediction)}
            for team_data in division_data["teams"]:
                team_data["predictions"][user] = pred_map.get(team_data["id"], "-")
                # ここでは簡略化のため、チームごとの反転数は表示しない

        results["divisions"].append(division_data)

        # 全地区を処理したらループを抜ける (例示用)
        break

    # 3. data.jsonに保存
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("data.json updated successfully.")

if __name__ == "__main__":
    main()