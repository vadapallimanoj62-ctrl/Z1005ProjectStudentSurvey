import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2 import service_account
from googleapiclient.discovery import build

def load_data():
    """Load data from Google Sheets or local file"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
    SERVICE_ACCOUNT_FILE = 'choticlg-3a6c2de58fdb.json'
    SPREADSHEET_ID = '1F-rTTDLA6TInDEsmbMB_OqkRYIof7_4p8S-U3zu08Uc'
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)
        
        try:
            sheet_metadata = service.spreadsheets().get(spreadsheetId=SPREADSHEET_ID).execute()
            sheet_name = sheet_metadata['sheets'][0]['properties']['title']
            RANGE_NAME = f"'{sheet_name}'!A1:Z1000"
            
            result = service.spreadsheets().values().get(
                spreadsheetId=SPREADSHEET_ID,
                range=RANGE_NAME
            ).execute()
            
            values = result.get('values', [])
            if not values:
                st.error('No data found in the spreadsheet')
                return None
                
            df = pd.DataFrame(values[1:], columns=values[0])
            return df
            
        except Exception as e:
            st.error(f"Error accessing sheet: {str(e)}")
            df = pd.read_csv('paste-2.txt', sep='\t')
            return df
            
    except Exception as e:
        st.error(f"Error with credentials: {str(e)}")
        df = pd.read_csv('paste-2.txt', sep='\t')
        return df

def clean_data(df):
    """Clean and prepare data for visualization"""
    # Find all rating/satisfaction columns
    rating_columns = [col for col in df.columns if 
                     any(word in col.lower() for word in ['rate', 'satisfied', 'satisfaction'])]
    
    # Convert ratings to numeric
    for col in rating_columns:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            continue
    
    # Convert timestamp
    if 'Timestamp' in df.columns:
        df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    return df

def find_column_by_keywords(df, keywords):
    """Find a column containing any of the given keywords"""
    for col in df.columns:
        if any(keyword.lower() in col.lower() for keyword in keywords):
            return col
    return None

def create_satisfaction_radar_chart(df):
    """Create radar chart for satisfaction metrics"""
    satisfaction_columns = [col for col in df.columns if 
                          ('satisfied' in col.lower() or 'satisfaction' in col.lower()) and 
                          ('rate' in col.lower() or 'how' in col.lower())]
    
    if not satisfaction_columns:
        return None
        
    numeric_data = {}
    for col in satisfaction_columns:
        try:
            numeric_data[col] = pd.to_numeric(df[col], errors='coerce').mean()
        except:
            continue
    
    satisfaction_columns = list(numeric_data.keys())
    if not satisfaction_columns:
        return None
    
    labels = []
    for col in satisfaction_columns:
        if 'with' in col:
            label = col.split('with ')[-1].split('?')[0]
        else:
            label = col.split('?')[0].split('rate')[-1].strip()
        labels.append(label)
    
    fig = go.Figure(data=go.Scatterpolar(
        r=list(numeric_data.values()),
        theta=labels,
        fill='toself'
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        showlegend=False,
        title='Average Satisfaction Metrics'
    )
    return fig

def create_demographic_chart(df, demographic_type):
    """Create pie chart for demographics"""
    demo_col = find_column_by_keywords(df, [demographic_type])
    if demo_col:
        counts = df[demo_col].value_counts()
        fig = px.pie(values=counts.values, names=counts.index, 
                    title=f'{demographic_type} Distribution')
        return fig
    return None

def create_club_participation_chart(df):
    """Create bar chart for club participation"""
    club_col = find_column_by_keywords(df, ['club', 'clubs', 'currently part'])
    if not club_col:
        return None
        
    # Split multiple selections and count occurrences
    all_clubs = []
    for clubs in df[club_col].dropna():
        all_clubs.extend([club.strip() for club in clubs.split(',')])
    
    club_counts = pd.Series(all_clubs).value_counts()
    
    fig = px.bar(
        x=club_counts.index,
        y=club_counts.values,
        title='Club Participation Distribution'
    )
    fig.update_layout(
        xaxis_title="Club",
        yaxis_title="Number of Students"
    )
    return fig

def create_future_plans_chart(df):
    """Create pie chart for future plans"""
    future_col = find_column_by_keywords(df, ['plan to pursue', 'after graduation'])
    if not future_col:
        return None
        
    plans = df[future_col].value_counts()
    fig = px.pie(values=plans.values, names=plans.index, 
                 title='Future Plans After Graduation')
    return fig

def create_mess_satisfaction_chart(df):
    """Create box plot for mess satisfaction"""
    mess_columns = [col for col in df.columns if 
                   'mess' in col.lower() and 
                   any(word in col.lower() for word in ['satisfied', 'satisfaction', 'rate'])]
    
    if not mess_columns:
        return None
        
    fig = px.box(df, y=mess_columns, title='Mess Satisfaction Distribution')
    return fig

def main():
    st.title('Student Feedback Dashboard')
    
    # Load and clean data
    df = load_data()
    if df is not None:
        df = clean_data(df)
        
        # Display column names for debugging
        if st.checkbox("Show available columns"):
            st.write("Available columns:", df.columns.tolist())
        
        # Basic statistics
        st.header('Overview')
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Responses", len(df))
        
        campus_col = find_column_by_keywords(df, ['campus facilities'])
        if campus_col:
            with col2:
                avg_campus = pd.to_numeric(df[campus_col], errors='coerce').mean()
                st.metric("Campus Satisfaction", f"{avg_campus:.2f}/5")
        
        teaching_col = find_column_by_keywords(df, ['teaching quality'])
        if teaching_col:
            with col3:
                avg_teaching = pd.to_numeric(df[teaching_col], errors='coerce').mean()
                st.metric("Teaching Quality", f"{avg_teaching:.2f}/5")
        
        # Satisfaction Metrics
        st.header('Satisfaction Metrics')
        satisfaction_chart = create_satisfaction_radar_chart(df)
        if satisfaction_chart:
            st.plotly_chart(satisfaction_chart, use_container_width=True)
        
        # Demographics
        st.header('Demographics')
        col1, col2 = st.columns(2)
        
        with col1:
            gender_chart = create_demographic_chart(df, 'Gender')
            if gender_chart:
                st.plotly_chart(gender_chart, use_container_width=True)
        
        with col2:
            ethnicity_chart = create_demographic_chart(df, 'Ethnicity')
            if ethnicity_chart:
                st.plotly_chart(ethnicity_chart, use_container_width=True)
        
        # Club Participation
        st.header('Club Participation')
        clubs_chart = create_club_participation_chart(df)
        if clubs_chart:
            st.plotly_chart(clubs_chart, use_container_width=True)
        
        # Future Plans
        st.header('Future Plans')
        plans_chart = create_future_plans_chart(df)
        if plans_chart:
            st.plotly_chart(plans_chart, use_container_width=True)
        
        # Mess Satisfaction
        st.header('Mess Satisfaction')
        mess_chart = create_mess_satisfaction_chart(df)
        if mess_chart:
            st.plotly_chart(mess_chart, use_container_width=True)
        
        # Raw Data
        if st.checkbox('Show Raw Data'):
            st.subheader('Raw Data')
            st.dataframe(df)

if __name__ == '__main__':
    main()

#https://docs.google.com/spreadsheets/d/1F-rTTDLA6TInDEsmbMB_OqkRYIof7_4p8S-U3zu08Uc/edit?usp=sharing