import geopandas as gpd
import pandas as pd
import folium
from folium.plugins import Draw
import streamlit as st
from streamlit_folium import folium_static
import seaborn as sns

# 读取数据
shapefile_path = "活动轨迹.shp"
csv_path = "陆家嘴问卷数据.csv"
gdf = gpd.read_file(shapefile_path)
df = pd.read_csv(csv_path)

# 合并GeoDataFrame和DataFrame
merged_gdf = gdf.merge(df, left_on="ID", right_on="ID")

# 获取所有字段名
field_names = merged_gdf.columns.tolist()

# Streamlit界面
st.sidebar.header("筛选器")

# 字段选择
selected_field = st.sidebar.selectbox("选择一个字段名", field_names)

# 唯一值选择
unique_values = merged_gdf[selected_field].unique()
selected_value = st.sidebar.selectbox("选择一个值", unique_values)

# 轨迹线样式选择
line_style = st.sidebar.selectbox("选择轨迹线样式", ["solid", "dashed", "dotted"])

# 轨迹颜色选择
trajectory_color = st.sidebar.color_picker("选择轨迹颜色", "#FF0000")  # 默认红色

# 颜色映射
unique_purposes = pd.unique(merged_gdf[['单次活动_活动目的', '活动目的_1st', '活动目的_2nd', '活动目的_3rd',
                                        '活动目的_4th', '活动目的_5th', '活动目的_6th', '活动目的_7th']].values.ravel('K'))
colors = sns.color_palette("husl", len(unique_purposes)).as_hex()
color_map = dict(zip(unique_purposes, colors))

# 活动目的颜色选择
st.sidebar.subheader("活动目的颜色")
for purpose in unique_purposes:
    color_map[purpose] = st.sidebar.color_picker(f"{purpose} 颜色", color_map[purpose])

def create_map(_filtered_gdf, trajectory_color, line_style, color_map):
    """创建地图并绘制筛选后的数据"""
    m = folium.Map(location=[31.2304, 121.4737], zoom_start=12, control_scale=True, tiles=None)  # 设置初始位置为上海, 不使用默认图层
    apikey = 'f87bf52d7c02e1ec3737d2b55fdb8d9d'
    tile_url = f"http://webrd02.is.autonavi.com/appmaptile?style=8&x={{x}}&y={{y}}&z={{z}}&lang=zh_cn&size=1&scl=1&ltype=11&client=android&apiKey={apikey}"
    folium.TileLayer(tiles=tile_url, attr='高德地图', opacity=0.8).add_to(m)
    Draw(export=True).add_to(m)

    for _, row in _filtered_gdf.iterrows():
        # 绘制轨迹线
        folium.GeoJson(
            row['geometry'],
            style_function=lambda x: {'color': trajectory_color, 'weight': 1.5,
                                      'dashArray': '5, 5' if line_style == 'dashed' else '1, 1' if line_style == 'dotted' else '1'}
        ).add_to(m)

        # 绘制空间点
        for col_x, col_y, purpose,locations_act, stime, etime in [
            ('单次活动_具体位置_x', '单次活动_具体位置_y', '单次活动_活动目的','单次活动_具体位置','单次活动_活动开始时间','单次活动_活动结束时间'),
            ('具体位置_1st_x', '具体位置_1st_y', '活动目的_1st','具体位置_1st','活动开始时间_1st','活动结束时间_1st'),
            ('具体位置_2nd_x', '具体位置_2nd_y', '活动目的_2nd','具体位置_2nd','活动开始时间_2nd','活动结束时间_2nd'),
            ('具体位置_3rd_x', '具体位置_3rd_y', '活动目的_3rd','具体位置_3rd','活动开始时间_3rd','活动结束时间_3rd'),
            ('具体位置_4th_x', '具体位置_4th_y', '活动目的_4th','具体位置_4th','活动开始时间_4th','活动结束时间_4th'),
            ('具体位置_5th_x', '具体位置_5th_y', '活动目的_5th','具体位置_5th','活动开始时间_5th','活动结束时间_5th'),
            ('具体位置_6th_x', '具体位置_6th_y', '活动目的_6th','具体位置_6th','活动开始时间_6th','活动结束时间_6th'),
            ('具体位置_7th_x', '具体位置_7th_y', '活动目的_7th','具体位置_7th','活动开始时间_7th','活动结束时间_7th')
        ]:
            if pd.notnull(row[col_x]) and pd.notnull(row[col_y]):

                def convert_time(time):
                    def format_time(variable):
                        if isinstance(variable, (int, float)) and 0 <= variable <= 96:
                            hours = int(variable // 4)
                            minutes = int((variable % 4) * 15)
                            return f"{hours:02d}:{minutes:02d}"
                        return ""

                    time = format_time(time)
                    return time

                popup_html = f"""
                            <div style='font-size:10px; white-space: nowrap;'>
                                <div>{purpose}:</div>
                                <div>{row[purpose]}</div>
                                <div>{locations_act}</div>
                                <div>{row[locations_act]}</div>
                                <div>{convert_time(row[stime])}——{convert_time(row[etime])}</div>
                            </div>
                            """
                folium.CircleMarker(
                    location=[row[col_y], row[col_x]],
                    radius=5,
                    color=color_map[row[purpose]],
                    fill=True,
                    fill_color=color_map[row[purpose]],
                    fill_opacity=0.6,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)

        # 绘制起点
        if pd.notnull(row['上一地点_具体位置_x']) and pd.notnull(row['上一地点_具体位置_y']):
            popup_html_start = f"""
                                <div style='font-size:9px; white-space: nowrap;'>
                                    <div>上一地点_地点类型:</div>
                                    <div>{row['上一地点_地点类型']}</div>
                                    <br>
                                    <div>{row["上一地点_具体位置"]}</div>
                                </div>
                                """
            folium.RegularPolygonMarker(
                location=[row['上一地点_具体位置_y'], row['上一地点_具体位置_x']],
                number_of_sides=3,
                radius=6,
                color='peru',
                fill=True,
                fill_color='peru',
                fill_opacity=0.6,
                popup=folium.Popup(popup_html_start, max_width=300)
            ).add_to(m)

        # 绘制终点
        if pd.notnull(row['下一地点_具体位置_x']) and pd.notnull(row['下一地点_具体位置_y']):
            popup_html_end = f"""
                                <div style='font-size:9px; white-space: nowrap;'>
                                    <div>下一地点_地点类型:</div>
                                    <div>{row['下一地点_地点类型']}</div>
                                    <br>
                                    <div>{row["下一地点_具体位置"]}</div>
                                </div>
                                """
            folium.RegularPolygonMarker(
                location=[row['下一地点_具体位置_y'], row['下一地点_具体位置_x']],
                number_of_sides=4,
                radius=6,
                color='teal',
                fill=True,
                fill_color='teal',
                fill_opacity=0.6,
                popup=folium.Popup(popup_html_end, max_width=300)
            ).add_to(m)

    return m

# 筛选数据
filtered_gdf = merged_gdf[merged_gdf[selected_field] == selected_value]

# 显示标题
st.sidebar.title("陆家嘴交互式GIS地图")

# 显示地图
st.sidebar.subheader(f"显示 {selected_field} 为 {selected_value} 的轨迹")
m = create_map(filtered_gdf, trajectory_color, line_style, color_map)
folium_static(m, width=1920, height=1080)

# 显示选中的数据及字段信息
st.sidebar.subheader(f"选中的数据和字段信息：{selected_field} = {selected_value}")
st.sidebar.write(filtered_gdf.T)  # 纵向显示
