"""全スレッドの投稿を日ごとにまとめ、トップ画面の集計値を作る。"""


def calculate_daily_rating_statistics(saved_posts, current_date):
    ratings_by_recorded_date = {}
    current_date_key = current_date.strftime("%Y-%m-%d")
    today_post_count = 0

    for saved_post in saved_posts:
        recorded_date = saved_post["created_at"][:10]
        if recorded_date == current_date_key:
            today_post_count += 1
        ratings_by_recorded_date.setdefault(recorded_date, []).append(int(saved_post["rating"]))

    average_rating_by_date = {
        recorded_date: sum(ratings_on_date) / len(ratings_on_date)
        for recorded_date, ratings_on_date in ratings_by_recorded_date.items()
    }
    # 投稿数が違う日も同じ重さで扱うため、日別平均をもう一度平均する。
    overall_average_rating = (
        sum(average_rating_by_date.values()) / len(average_rating_by_date)
        if average_rating_by_date
        else None
    )
    recorded_dates_in_order = sorted(average_rating_by_date)

    return {
        "today": current_date.strftime("%Y年%m月%d日"),
        "today_count": today_post_count,
        "today_average": average_rating_by_date.get(current_date_key),
        "overall_average": overall_average_rating,
        "chart_dates": recorded_dates_in_order,
        "chart_averages": [average_rating_by_date[recorded_date] for recorded_date in recorded_dates_in_order],
        "chart_counts": [len(ratings_by_recorded_date[recorded_date]) for recorded_date in recorded_dates_in_order],
    }
