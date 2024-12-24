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
    # Convert all columns to string first to handle mixed types
    df = df.astype(str)
    
    # Clean satisfaction/rating columns
    rating_cols = [col for col in df.columns if any(word in col.lower() 
                  for word in ['satisfied', 'satisfaction', 'rate'])]
    for col in rating_cols:
        try:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        except:
            continue
    
    return df

def create_section_header(title, description=""):
    """Create a styled section header"""
    st.markdown(f"""
    <div style='background-color: #1e1e1e; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0;'>
        <h2 style='color: #ffffff; margin-bottom: 0.5rem;'>{title}</h2>
        <p style='color: #cccccc;'>{description}</p>
    </div>
    """, unsafe_allow_html=True)

def create_satisfaction_metrics(df):
    """Create satisfaction metrics visualization"""
    satisfaction_cols = {
        'courses offered/taught': 'How would you rate your overall satisfaction with courses offered/taught?',
        'your current studies': 'How would you rate your overall satisfaction with your current studies?',
        'teaching quality': 'How would you rate your overall satisfaction with teaching quality?',
        'course assessment': 'How would you rate your overall satisfaction with course assessment instructions?',
        'mess menu': 'How satisfied are you with the mess menu?',
        'mess food quality': 'How satisfied are you with the mess food quality?',
        'campus facilities': 'How satisfied are you with the college campus facilities?'
    }
    
    # Calculate averages
    values = {}
    for label, col in satisfaction_cols.items():
        if col in df.columns:
            avg = pd.to_numeric(df[col], errors='coerce').mean()
            values[label] = avg if not pd.isna(avg) else 0

    # Create radar chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(values.values()),
        theta=list(values.keys()),
        fill='toself',
        fillcolor='rgba(64, 132, 244, 0.3)',
        line=dict(color='#4084f4')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )
        ),
        showlegend=False,
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#1e1e1e',
        font=dict(color='#ffffff')
    )
    
    return fig

def create_key_metrics_summary(df):
    """Create summary of key metrics"""
    metrics = {}
    
    # Academic metrics
    academic_cols = [col for col in df.columns if any(word in col.lower() 
                    for word in ['studies', 'courses', 'teaching'])]
    academic_ratings = pd.DataFrame()
    for col in academic_cols:
        academic_ratings[col] = pd.to_numeric(df[col], errors='coerce')
    
    metrics['Academic Satisfaction'] = {
        'mean': academic_ratings.mean().mean(),
        'median': academic_ratings.median().median()
    }
    
    # Mess metrics
    mess_cols = [col for col in df.columns if 'mess' in col.lower()]
    mess_ratings = pd.DataFrame()
    for col in mess_cols:
        mess_ratings[col] = pd.to_numeric(df[col], errors='coerce')
    
    metrics['Mess Satisfaction'] = {
        'mean': mess_ratings.mean().mean(),
        'median': mess_ratings.median().median()
    }
    
    # Campus facilities metrics
    facilities_col = 'How satisfied are you with the college campus facilities?'
    if facilities_col in df.columns:
        facilities_ratings = pd.to_numeric(df[facilities_col], errors='coerce')
        metrics['Campus Satisfaction'] = {
            'mean': facilities_ratings.mean(),
            'median': facilities_ratings.median()
        }
    
    return metrics

def create_category_comparison(df):
    """Create category-wise comparison visualization"""
    categories = {
        'Academic': ['studies', 'courses', 'teaching'],
        'Campus': ['facilities', 'campus'],
        'Mess': ['mess', 'food'],
    }
    
    category_scores = {}
    for category, keywords in categories.items():
        cols = [col for col in df.columns if any(word in col.lower() for word in keywords)]
        ratings = pd.DataFrame()
        for col in cols:
            ratings[col] = pd.to_numeric(df[col], errors='coerce')
        category_scores[category] = ratings.mean().mean()
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(category_scores.keys()),
            y=list(category_scores.values()),
            marker_color=['#4084f4', '#40c463', '#ff7b72']
        )
    ])
    
    fig.update_layout(
        title='Category-wise Average Satisfaction',
        paper_bgcolor='#1e1e1e',
        plot_bgcolor='#1e1e1e',
        font=dict(color='#ffffff'),
        xaxis=dict(title='Category'),
        yaxis=dict(title='Average Rating', range=[0, 5])
    )
    
    return fig



def clean_text(text):
    """Clean text by removing etc and extra spaces"""
    return text.strip().replace('etc.', '').replace('etc', '').strip()

def analyze_campus_feedback(df):
    """Analyze campus feedback showing all responses in descending order"""
    
    # Create columns
    cols = st.columns(2)
    
    with cols[0]:
        # Process liked aspects
        like_col = 'What aspects of the campus do you like the most? (Select all that apply)'
        
        # Initialize list for all responses
        all_responses = []
        
        # Process each response
        for response in df[like_col].dropna():
            # Split responses, clean them and remove etc
            aspects = [clean_text(aspect) for aspect in response.split(',')]
            all_responses.extend(aspects)
        
        # Create counts for all responses
        response_counts = pd.Series(all_responses).value_counts()
        
        # Create visualization DataFrame
        liked_viz_data = pd.DataFrame({
            'Aspect': response_counts.index,
            'Count': response_counts.values,
            'Percentage': [round((count / len(df) * 100), 1) for count in response_counts.values]
        })
        
        # Clean aspect names - remove empty counts and format text
        liked_viz_data['Aspect'] = liked_viz_data['Aspect'].apply(
            lambda x: clean_text(x.strip()
                      .replace(': 0 responses (0.0%)', '')
                      .replace(' responses', '')
                      .replace('(', '')
                      .replace(')', '')
                      .replace(':', ''))
        )
        
        # Remove any empty rows that might have been created by cleaning
        liked_viz_data = liked_viz_data[liked_viz_data['Aspect'].str.len() > 0]
        
        # Create visualization
        liked_fig = px.bar(
            data_frame=liked_viz_data,
            x='Count',
            y='Aspect',
            orientation='h',
            text='Percentage',
            title='Most Liked Campus Aspects',
            labels={'Count': 'Number of Responses', 'Aspect': ''}
        )
        
        liked_fig.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside'
        )
        liked_fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            yaxis={'categoryorder': 'total descending'}  # Sort in descending order
        )
        
        st.plotly_chart(liked_fig, use_container_width=True)
    
    with cols[1]:
        # Process improvements needed
        improve_col = 'What aspects of the campus do you think need improvement? (Select all that apply)'
        
        # Initialize list for all responses
        all_improvements = []
        
        # Process each response
        for response in df[improve_col].dropna():
            # Split responses, clean them and remove etc
            aspects = [clean_text(aspect) for aspect in response.split(',')]
            all_improvements.extend(aspects)
        
        # Create counts for all responses
        improvement_counts = pd.Series(all_improvements).value_counts()
        
        # Create visualization DataFrame
        improvement_viz_data = pd.DataFrame({
            'Aspect': improvement_counts.index,
            'Count': improvement_counts.values,
            'Percentage': [round((count / len(df) * 100), 1) for count in improvement_counts.values]
        })
        
        # Clean aspect names
        improvement_viz_data['Aspect'] = improvement_viz_data['Aspect'].apply(
            lambda x: clean_text(x.strip()
                      .replace(': 0 responses (0.0%)', '')
                      .replace(' responses', '')
                      .replace('(', '')
                      .replace(')', '')
                      .replace(':', ''))
        )
        
        # Remove any empty rows that might have been created by cleaning
        improvement_viz_data = improvement_viz_data[improvement_viz_data['Aspect'].str.len() > 0]
        
        # Create visualization
        improvement_fig = px.bar(
            data_frame=improvement_viz_data,
            x='Count',
            y='Aspect',
            orientation='h',
            text='Percentage',
            title='Aspects Needing Improvement',
            labels={'Count': 'Number of Responses', 'Aspect': ''}
        )
        
        improvement_fig.update_traces(
            texttemplate='%{text:.1f}%',
            textposition='outside'
        )
        improvement_fig.update_layout(
            margin=dict(l=20, r=20, t=40, b=20),
            showlegend=False,
            yaxis={'categoryorder': 'total descending'}  # Sort in descending order
        )
        
        st.plotly_chart(improvement_fig, use_container_width=True)


def analyze_future_plans(df):
    """Analyze and visualize future plans data"""
    # Create columns for the visualizations
    cols = st.columns(3)
    
    with cols[0]:
        # General future plans
        future_plans = df['Which field do you plan to pursue after graduation?  '].value_counts()
        total_responses = len(df)
        percentages = (future_plans / total_responses) * 100
        total_responses = len(df)

        # Create pie chart for future plans
        plans_fig = go.Figure(data=[go.Pie(
            labels=future_plans.index,
            values=future_plans.values,
            hole=0.4,
            customdata=[(count/total_responses*100) for count in future_plans.values],
            texttemplate='%{customdata:.1f}%',
            textposition='outside',
        
            hovertemplate='%{label}<br>%{value} responses<br>%{percent:.1f}%<extra></extra>'
        )])
        plans_fig.update_layout(
            title='Future Plans After Graduation',
            showlegend=False,
            paper_bgcolor='#1e1e1e',
            plot_bgcolor='#1e1e1e',
            font=dict(color='white'),
            height=400
        )
        st.plotly_chart(plans_fig, use_container_width=True)
    
    with cols[1]:
        # Higher studies majors
        majors = df['If applying to higher studies, which major you shall be pursuing?'].value_counts()
        total_major_responses = len(df[df['If applying to higher studies, which major you shall be pursuing?'].notna()])
        percentages = (majors / total_major_responses) * 100
        
        # Create pie chart for higher studies majors
        majors_fig = go.Figure(data=[go.Pie(
            labels=majors.index,
            values=majors.values,
            hole=0.4,
            textinfo='value+percent',
            textposition='outside',
            texttemplate='%{value} (%{percent:.1f}%)',
            hovertemplate='%{label}<br>%{value} responses<br>%{percent:.1f}%<extra></extra>'
        )])
        majors_fig.update_layout(
            title='Intended Major for Higher Studies',
            showlegend=False,
            paper_bgcolor='#1e1e1e',
            plot_bgcolor='#1e1e1e',
            font=dict(color='white'),
            height=400
        )
        st.plotly_chart(majors_fig, use_container_width=True)
    
    with cols[2]:
        # Job sectors
        sectors_col = 'If applying to job, research, which sectors you are interested in most? (select all that apply)'
        
        # Initialize list for all responses
        all_sectors = []
        
        # Process each response
        for response in df[sectors_col].dropna():
            # Split responses and clean them
            sectors = [sector.strip() for sector in response.split(',')]
            # Remove any empty responses or 'etc'
            sectors = [s for s in sectors if s and s.lower() != 'etc' and s.lower() != 'etc.']
            all_sectors.extend(sectors)
        
        # Create counts for all responses
        sector_counts = pd.Series(all_sectors).value_counts()
        total_sector_responses = len(all_sectors)
        percentages = (sector_counts / total_sector_responses) * 100
        
        # Create pie chart for job sectors
        sectors_fig = go.Figure(data=[go.Pie(
            labels=sector_counts.index,
            values=sector_counts.values,
            hole=0.4,
            textinfo='value+percent',
            textposition='outside',
            texttemplate='%{value} (%{percent:.1f}%)',
            hovertemplate='%{label}<br>%{value} responses<br>%{percent:.1f}%<extra></extra>'
        )])
        sectors_fig.update_layout(
            title='Preferred Job/Research Sectors',
            showlegend=False,
            paper_bgcolor='#1e1e1e',
            plot_bgcolor='#1e1e1e',
            font=dict(color='white'),
            height=400
        )
        st.plotly_chart(sectors_fig, use_container_width=True)

    # Display additional metrics
    st.markdown("### Key Statistics")
    metric_cols = st.columns(3)
    
    with metric_cols[0]:
        higher_studies_count = len(df[df['Which field do you plan to pursue after graduation?  '] == 'Higher Studies'])
        st.metric("Higher Studies Interest", f"{(higher_studies_count/total_responses)*100:.1f}%")
    
    with metric_cols[1]:
        corporate_count = len(df[df['Which field do you plan to pursue after graduation?  '] == 'Corporate Job'])
        st.metric("Corporate Job Interest", f"{(corporate_count/total_responses)*100:.1f}%")
    
    with metric_cols[2]:
        research_count = len(df[df['Which field do you plan to pursue after graduation?  '] == 'Research'])
        st.metric("Research Interest", f"{(research_count/total_responses)*100:.1f}%")



def analyze_additional_feedback(df):
    """Analyze and visualize additional feedback including campus recommendations"""
    # Create section header
    create_section_header("Additional Feedback", 
                         "Analysis of campus recommendations and additional suggestions")
    
    # Create columns
    cols = st.columns(2)
    
    with cols[0]:
        # Get recommendation data
        recommend_data = df['Would you recommend IIT Madras Zanzibar campus to others? '].value_counts()
        total_responses = recommend_data.sum()
        recommend_percentages = (recommend_data / total_responses * 100).round(1)
        
        # Create pie chart for recommendations
        recommend_fig = go.Figure(data=[go.Pie(
            labels=recommend_data.index,
            values=recommend_percentages,
            hole=0.4,
            textinfo='percent',
            textposition='inside',
            texttemplate='%{value:.1f}%',
            marker=dict(colors=['#4169E1', '#DC143C', '#FFA500']),  # Blue, Red, Orange for Yes, No, Maybe
            hovertemplate='%{label}<br>Percentage: %{value:.1f}%<extra></extra>'
        )])
        
        recommend_fig.update_layout(
            title='Would you recommend IIT Madras Zanzibar campus to others?',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            paper_bgcolor='#1e1e1e',
            plot_bgcolor='#1e1e1e',
            font=dict(color='#ffffff'),
            height=400
        )
        st.plotly_chart(recommend_fig, use_container_width=True)
    
    with cols[1]:
        # Display key insights or additional information
        st.markdown("""
        ### Key Insights
        - Majority of students would recommend the campus
        - Shows overall satisfaction with campus experience
        - Indicates areas for potential improvement
        
        ### Additional Comments
        Student feedback highlights several areas for improvement:
        - Campus facilities and infrastructure
        - Academic resources and support
        - Extra-curricular activities
        """)


def analyze_campus_clubs(df):
    """Analyze and visualize campus clubs data"""
    
    def create_horizontal_bar(data, column_name, title):
        # Get value counts and calculate percentages
        counts = df[column_name].str.split(',').explode().str.strip().value_counts()
        percentages = (counts / len(df) * 100).round(1)
        
        # Create figure
        fig = go.Figure()
        
        # Add bars
        fig.add_trace(go.Bar(
            x=counts.values,
            y=counts.index,
            orientation='h',
            marker=dict(color='#8B4513'),  # Brown color matching screenshot
            text=[f"{count} ({pct}%)" for count, pct in zip(counts.values, percentages.values)],
            textposition='outside'
        ))
        
        # Update layout
        fig.update_layout(
            title=title,
            showlegend=False,
            xaxis=dict(
                title='',
                showgrid=False,
                range=[0, max(counts.values) * 1.2]  # Add 20% padding for labels
            ),
            yaxis=dict(
                title='',
                autorange="reversed"  # Reverse the order to match screenshot
            ),
            margin=dict(l=0, r=100, t=30, b=0),  # Adjust margins
            height=400
        )
        
        return fig
    
    # Create club membership visualization
    membership_fig = create_horizontal_bar(
        df,
        'Which college club(s) are you currently part of? (Select all that apply)',
        'Club Membership Distribution'
    )
    st.plotly_chart(membership_fig, use_container_width=True)
    
    # Create beneficial events visualization
    beneficial_fig = create_horizontal_bar(
        df,
        'Which clubs\' events have you found most beneficial? (select all that apply)',
        'Most Beneficial Club Events'
    )
    st.plotly_chart(beneficial_fig, use_container_width=True)
    
    # Create new clubs interest pie chart
    new_clubs = df['Would  you like to introduce new clubs in the campus?'].value_counts()
    new_clubs_pct = (new_clubs / len(df) * 100).round(1)
    total_responses = len(df)

    clubs_fig = go.Figure(data=[go.Pie(
        labels=new_clubs.index,
        values=new_clubs.values,
        hole=0.4,
        textinfo='percent',
        textposition='inside',
        customdata=[(count/total_responses*100) for count in new_clubs.values],
        texttemplate='%{customdata:.1f}%',
        marker=dict(colors=['#4169E1', '#DC143C', '#FFA500']),  # Blue, Red, Orange
        showlegend=True
    )])
    
    clubs_fig.update_layout(
        title='Interest in New Clubs',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=400
    )
    
    st.plotly_chart(clubs_fig, use_container_width=True)



def main():
    st.set_page_config(layout="wide")
    
    # Custom CSS for styling
    st.markdown("""
        <style>
        .stApp {
            max-width: 1200px;
            margin: 0 auto;
        }
        .st-emotion-cache-1v0mbdj {
            width: 100%;
        }
        div[data-testid="stMetricValue"] {
            font-size: 24px;
        }
        div[data-testid="stMetricDelta"] {
            font-size: 16px;
        }
        div.stMarkdown h2 {
            font-size: 1.5em;
            margin-top: 1em;
            margin-bottom: 0.5em;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title('🎓 Student Survey Analytics Dashboard')
    
    # Load and clean data
    df = load_data()
    if df is not None:
        df = clean_data(df)
        
        # Key Metrics Section
        create_section_header("Key Statistics", "Overview of satisfaction metrics across categories")
        
        metrics = create_key_metrics_summary(df)
        
        # Add total responses count
        total_responses = len(df)+1
        
        # Create one more column for total responses
        cols = st.columns(len(metrics) + 1)  # Added +1 for total responses
        
        # First display total responses
        with cols[0]:
            st.metric(
                "Total Responses",
                f"{total_responses:,}",  # Format with comma for thousands
                ""  # No delta value for total responses
            )
        
        # Then display other metrics
        for col, (category, values) in zip(cols[1:], metrics.items()):
            with col:
                st.metric(
                    f"{category}",
                    f"{values['mean']:.2f}/5",
                    f"Median: {values['median']:.2f}"
                )
        
        # Satisfaction Radar Chart
        create_section_header("Overall Satisfaction Analysis", 
                            "Comprehensive view of satisfaction across different aspects")
        satisfaction_fig = create_satisfaction_metrics(df)
        st.plotly_chart(satisfaction_fig, use_container_width=True)
        
        # Category Comparison
        category_fig = create_category_comparison(df)
        st.plotly_chart(category_fig, use_container_width=True)
        
        # Demographics Section
        create_section_header("Demographics", "Student population distribution")
        
        # Row 1: Gender and Ethnicity
        demo_row1_col1, demo_row1_col2 = st.columns(2)
        
        with demo_row1_col1:
            gender_fig = px.pie(
                values=df['Gender'].value_counts().values,
                names=df['Gender'].value_counts().index,
                title='Gender Distribution',
                hole=0.4
            )
            gender_fig.update_layout(showlegend=True)
            st.plotly_chart(gender_fig, use_container_width=True)
        
        with demo_row1_col2:
            ethnicity_fig = px.pie(
                values=df['Ethnicity'].value_counts().values,
                names=df['Ethnicity'].value_counts().index,
                title='Ethnicity Distribution',
                hole=0.4
            )
            ethnicity_fig.update_layout(showlegend=True)
            st.plotly_chart(ethnicity_fig, use_container_width=True)
        
        # Row 2: Degree and Major
        demo_row2_col1, demo_row2_col2 = st.columns(2)
        
        with demo_row2_col1:
            degree_fig = px.pie(
                values=df['What degree are you currently pursuing?'].value_counts().values,
                names=df['What degree are you currently pursuing?'].value_counts().index,
                title='Degree Distribution',
                hole=0.4
            )
            degree_fig.update_layout(showlegend=True)
            st.plotly_chart(degree_fig, use_container_width=True)
        
        with demo_row2_col2:
            major_fig = px.pie(
                values=df['What is your major?'].value_counts().values,
                names=df['What is your major?'].value_counts().index,
                title='Major Distribution',
                hole=0.4
            )
            major_fig.update_layout(showlegend=True)
            st.plotly_chart(major_fig, use_container_width=True)
        
        # Row 3: Graduation Year
        grad_year_fig = px.bar(
            x=df['What is your expected graduation year?'].value_counts().index,
            y=df['What is your expected graduation year?'].value_counts().values,
            title='Expected Graduation Year Distribution',
            labels={'x': 'Graduation Year', 'y': 'Number of Students'}
        )
        grad_year_fig.update_layout(
            xaxis_title="Graduation Year",
            yaxis_title="Number of Students",
            showlegend=False
        )
        st.plotly_chart(grad_year_fig, use_container_width=True)
        
        # Campus Experience Section
        create_section_header("Campus Experience", 
                     "Analysis of campus facilities and feedback")


        analyze_campus_feedback(df)

        campus_cols = [col for col in df.columns if 'campus' in col.lower()]
        
        for col in campus_cols:
            if not any(word in col.lower() for word in ['feedback', 'improve']):
                values = pd.to_numeric(df[col], errors='coerce')
                fig = go.Figure()
                
                fig.add_trace(go.Histogram(
                    x=values,
                    nbinsx=5,
                    name='Distribution',
                    marker_color='#4084f4'
                ))
                
                fig.add_trace(go.Box(
                    x=values,
                    name='Box Plot',
                    marker_color='#40c463'
                ))
                
                fig.update_layout(
                    title=col,
                    paper_bgcolor='#1e1e1e',
                    plot_bgcolor='#1e1e1e',
                    font=dict(color='#ffffff'),
                    showlegend=True
                )
                
                st.plotly_chart(fig, use_container_width=True)

        # Facility Satisfaction Distribution
        facility_satisfaction = df['How satisfied are you with the college campus facilities?'].value_counts()
        satisfaction_fig = px.bar(
            x=facility_satisfaction.index,
            y=facility_satisfaction.values,
            text=[f"{(v/len(df)*100):.1f}%" for v in facility_satisfaction.values],
            title='Satisfaction with Campus Facilities',
            labels={'x': 'Rating', 'y': 'Number of Responses'}
        )
        satisfaction_fig.update_traces(textposition='outside')
        satisfaction_fig.update_xaxes(type='category')
        st.plotly_chart(satisfaction_fig, use_container_width=True)
        
        # Liked Aspects
      
        create_section_header("Future Plans", 
                     "Analysis of Future Plans")


        analyze_future_plans(df)
            
           
                
            
        # Academic Section
        create_section_header("Academic Experience", 
                            "Analysis of academic satisfaction and performance")
        
        academic_cols = [col for col in df.columns if any(word in col.lower() 
                        for word in ['studies', 'courses', 'teaching'])]
        
        for col in academic_cols:
            values = pd.to_numeric(df[col], errors='coerce')
            fig = go.Figure()
            
            # Add histogram
            fig.add_trace(go.Histogram(
                x=values,
                nbinsx=5,
                name='Distribution',
                marker_color='#4084f4'
            ))
            
            # Add box plot
            fig.add_trace(go.Box(
                x=values,
                name='Box Plot',
                marker_color='#40c463'
            ))
            
            fig.update_layout(
                title=col,
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='#ffffff'),
                showlegend=True
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Mess Experience Section
        # Mess Experience Section
        create_section_header("Mess Experience", 
                            "Analysis of mess satisfaction and food quality (1: Poor to 5: Excellent)")

        # Create two rows with columns
        row1_cols = st.columns(2)
        row2_cols = st.columns(2)

        # First row
        with row1_cols[0]:
            menu_data = df['How satisfied are you with the mess menu?'].value_counts()
            total_menu_responses = menu_data.sum()
            menu_percentages = (menu_data / total_menu_responses * 100).round(1)
            
            menu_fig = go.Figure(data=[go.Pie(
                labels=menu_data.index,
                values=menu_percentages,  # Use calculated percentages
                hole=0.4,
                textinfo='percent',
                textposition='inside',
                texttemplate='%{value:.1f}%',  # Show calculated percentage
                hovertemplate='Rating: %{label}<br>Percentage: %{value:.1f}%<extra></extra>'
            )])
            menu_fig.update_layout(
                title='Mess Menu Satisfaction',
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='#ffffff'),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(menu_fig, use_container_width=True)

        with row1_cols[1]:
            quality_data = df['How satisfied are you with the mess food quality?'].value_counts()
            total_quality_responses = quality_data.sum()
            quality_percentages = (quality_data / total_quality_responses * 100).round(1)
            
            quality_fig = go.Figure(data=[go.Pie(
                labels=quality_data.index,
                values=quality_percentages,  # Use calculated percentages
                hole=0.4,
                textinfo='percent',
                textposition='inside',
                texttemplate='%{value:.1f}%',  # Show calculated percentage
                hovertemplate='Rating: %{label}<br>Percentage: %{value:.1f}%<extra></extra>'
            )])
            quality_fig.update_layout(
                title='Food Quality Satisfaction',
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='#ffffff'),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(quality_fig, use_container_width=True)

        # Second row - Food Preference
        with row2_cols[0]:
            food_pref = df['Food preference'].value_counts()
            total_pref_responses = food_pref.sum()
            pref_percentages = (food_pref / total_pref_responses * 100).round(1)
            
            pref_fig = go.Figure(data=[go.Pie(
                labels=food_pref.index,
                values=pref_percentages,  # Use calculated percentages
                hole=0.4,
                textinfo='percent',
                textposition='inside',
                texttemplate='%{value:.1f}%',  # Show calculated percentage
                marker=dict(colors=['#4169E1', '#DC143C']),  # Blue for Veg, Red for Non-veg
                hovertemplate='%{label}<br>Percentage: %{value:.1f}%<extra></extra>'
            )])
            pref_fig.update_layout(
                title='Food Preference',
                paper_bgcolor='#1e1e1e',
                plot_bgcolor='#1e1e1e',
                font=dict(color='#ffffff'),
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )
            st.plotly_chart(pref_fig, use_container_width=True)

        # Add rating scale explanation in the second column
        with row2_cols[1]:
            st.markdown("""
            ### Rating Scale Guide
            🔵 1 - Poor
            🔵 2 - Below Average
            🔵 3 - Average
            🔵 4 - Good
            🔵 5 - Excellent
            
            ### Key Insights
            - Shows satisfaction levels with mess menu and food quality
            - Displays distribution of dietary preferences
            - Rating of 1-5 indicates increasing levels of satisfaction
            """)

        create_section_header("Campus Life", 
                            "Analysis of campus facilities and activities")

        analyze_campus_clubs(df)

        # analyze_additional_feedback(df)
        
        # Campus Life Section
        
        
        

if __name__ == '__main__':
    main()

#https://docs.google.com/spreadsheets/d/1F-rTTDLA6TInDEsmbMB_OqkRYIof7_4p8S-U3zu08Uc/edit?usp=sharing
