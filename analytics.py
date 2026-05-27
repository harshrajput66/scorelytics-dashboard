import os
import tempfile
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_absolute_error

# Reportlab imports
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image

STREAM_SUBJECTS = {
    "Medical":     ["Physics", "Chemistry", "Biology", "English", "Physical Education"],
    "Non-Medical": ["Physics", "Chemistry", "Mathematics", "English", "Computer Science"],
    "Commerce":    ["Accountancy", "Business Studies", "Economics", "English", "Mathematics"],
    "Arts":        ["History", "Political Science", "Geography", "English", "Hindi"],
}
# Flat list of all unique subjects across all streams (used by the predictor)
SUBJECTS = sorted(set(s for subjs in STREAM_SUBJECTS.values() for s in subjs))

def get_grade(score):
    """Converts a numerical score to a letter grade based on Indian standards."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 40:
        return "D"
    else:
        return "F (Fail)"

def get_risk_status(avg_score, avg_attendance):
    """Determines student's risk category based on score and attendance."""
    if avg_score < 50 or avg_attendance < 75:
        return "High Risk", colors.HexColor("#D32F2F")  # Dark Red
    elif avg_score < 65 or avg_attendance < 80:
        return "Medium Risk", colors.HexColor("#F57C00")  # Orange
    else:
        return "Low Risk", colors.HexColor("#388E3C")  # Green

def calculate_school_stats(df):
    """Calculates overall school statistics from the performance dataframe."""
    if df.empty:
        return {}
        
    overall_avg = df["score"].mean()
    overall_attendance = df["attendance_rate"].mean()
    overall_study = df["study_hours_per_week"].mean()
    
    # Group by student to calculate student-level metrics
    student_avgs = df.groupby("student_id").agg({
        "score": "mean",
        "attendance_rate": "first"
    })
    
    total_students = len(student_avgs)
    
    # A student passes if their average score is >= 40
    passing_students = sum(student_avgs["score"] >= 40)
    pass_rate = (passing_students / total_students) * 100 if total_students > 0 else 0.0
    
    # Subject-wise statistics
    subj_stats = df.groupby("subject").agg(
        avg_score=("score", "mean"),
        avg_attendance=("attendance_rate", "mean")
    ).reset_index()
    
    return {
        "overall_avg": round(overall_avg, 2),
        "overall_attendance": round(overall_attendance, 2),
        "overall_study": round(overall_study, 2),
        "total_students": total_students,
        "pass_rate": round(pass_rate, 2),
        "subject_stats": subj_stats
    }

def train_predictive_model(df):
    """
    Trains a Linear Regression model to predict a student's score in a subject.
    Features: attendance_rate, study_hours_per_week, parental_involvement, extracurricular, subject
    """
    if df.empty or len(df) < 20:
        return None, 0.0, 0.0, {}, []
        
    df_ml = df.copy()
    
    # Map categorical features to numeric
    involvement_map = {"Low": 0, "Medium": 1, "High": 2}
    df_ml["ParentalInvolvementEncoded"] = df_ml["parental_involvement"].map(involvement_map)
    df_ml["ExtracurricularEncoded"] = df_ml["extracurricular"].map(lambda x: 1 if x == "Yes" else 0)
    
    # One-hot encode subject
    subject_dummies = pd.get_dummies(df_ml["subject"], prefix="Subj")
    dummy_cols = list(subject_dummies.columns)
    
    # Concatenate features
    features_base = ["attendance_rate", "study_hours_per_week", "ParentalInvolvementEncoded", "ExtracurricularEncoded"]
    X = pd.concat([df_ml[features_base], subject_dummies], axis=1)
    y = df_ml["score"]
    
    # Align Boolean and numeric types
    X = X.astype(float)
    
    # Train-test split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    
    # Metrics
    y_pred = model.predict(X_test)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    
    feature_names = list(X.columns)
    
    # Get coefficients mapping
    coef_dict = dict(zip(feature_names, model.coef_))
    
    return model, r2, mae, coef_dict, feature_names

def predict_student_score(model, feature_names, attendance, study_hours, parental_involvement, extracurricular, subject):
    """Predicts score using the trained linear model."""
    if model is None:
        return 50.0
        
    involvement_map = {"Low": 0, "Medium": 1, "High": 2}
    parental_enc = involvement_map.get(parental_involvement, 1)
    extra_enc = 1.0 if (extracurricular in ["Yes", True]) else 0.0
    
    # Setup record with zeros
    record = {col: 0.0 for col in feature_names}
    record["attendance_rate"] = float(attendance)
    record["study_hours_per_week"] = float(study_hours)
    record["ParentalInvolvementEncoded"] = float(parental_enc)
    record["ExtracurricularEncoded"] = float(extra_enc)
    
    # Set subject flag
    subj_col = f"Subj_{subject}"
    if subj_col in record:
        record[subj_col] = 1.0
        
    input_df = pd.DataFrame([record])[feature_names]
    pred = model.predict(input_df)[0]
    return round(float(np.clip(pred, 30.0, 100.0)), 1)

def generate_report_card_pdf(student_info, performance_df, overall_stats, file_path):
    """
    Generates a professional report card PDF for a student.
    Includes details, performance table, visual matplotlib bar chart, and teacher's notes.
    """
    # 1. Generate the comparison chart as a temporary PNG
    temp_dir = tempfile.gettempdir()
    chart_path = os.path.join(temp_dir, f"student_chart_{student_info['student_id']}.png")
    
    subjects = performance_df["subject"].tolist()
    student_scores = performance_df["score"].tolist()
    
    # Get school averages for the same subjects
    school_averages = []
    subject_stats_df = overall_stats.get("subject_stats", pd.DataFrame())
    
    for subj in subjects:
        if not subject_stats_df.empty and subj in subject_stats_df["subject"].values:
            avg = subject_stats_df[subject_stats_df["subject"] == subj]["avg_score"].values[0]
            school_averages.append(avg)
        else:
            school_averages.append(70.0)  # Fallback average
            
    # Draw Matplotlib Chart
    fig, ax = plt.subplots(figsize=(7, 3.2))
    x = np.arange(len(subjects))
    width = 0.35
    
    # Elegant custom palette (Hex colors matching reportlab styling)
    rects1 = ax.bar(x - width/2, student_scores, width, label='Student', color='#1F3A60')
    rects2 = ax.bar(x + width/2, school_averages, width, label='School Average', color='#A0B2C6')
    
    ax.set_ylabel('Scores', fontsize=9, fontweight='bold', color='#333333')
    ax.set_title('Subject Performance Comparison', fontsize=11, fontweight='bold', color='#1F3A60', pad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(subjects, fontsize=8, fontweight='bold')
    ax.set_ylim(0, 110)
    ax.legend(frameon=True, facecolor='#F8F9FA', edgecolor='none', fontsize=8)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#CCCCCC')
    ax.spines['bottom'].set_color('#CCCCCC')
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    
    # Value labels
    for rect in rects1:
        h = rect.get_height()
        ax.annotate(f'{int(h)}', xy=(rect.get_x() + rect.get_width()/2, h),
                    xytext=(0, 2), textcoords="offset points", ha='center', va='bottom', fontsize=8, color='#1F3A60', weight='bold')
                    
    plt.tight_layout()
    plt.savefig(chart_path, dpi=300)
    plt.close()
    
    # 2. Build PDF Document using ReportLab
    doc = SimpleDocTemplate(
        file_path,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#1F3A60'),
        alignment=1, # Center
        spaceAfter=5
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=1, # Center
        spaceAfter=15
    )
    
    section_title = ParagraphStyle(
        'SecTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#1F3A60'),
        spaceBefore=10,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        textColor=colors.HexColor('#333333'),
        leading=14
    )
    
    body_bold = ParagraphStyle(
        'BodyBoldCustom',
        parent=body_style,
        fontName='Helvetica-Bold'
    )
    
    header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=1
    )
    
    cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        alignment=1
    )

    story = []
    
    # Title / Letterhead
    story.append(Paragraph("SCORELYTICS", title_style))
    story.append(Paragraph("Academic Progress & Performance Report Card", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Student Info Table
    student_avg_score = performance_df["score"].mean()
    student_avg_attendance = performance_df["attendance_rate"].iloc[0]
    student_total_study = performance_df["study_hours_per_week"].iloc[0]
    parental_invol = performance_df["parental_involvement"].iloc[0]
    extra_curr = performance_df["extracurricular"].iloc[0]
    
    risk_cat, risk_color = get_risk_status(student_avg_score, student_avg_attendance)
    
    info_data = [
        [
            Paragraph("<b>Student Name:</b>", body_style), Paragraph(student_info['name'], body_bold),
            Paragraph("<b>Student ID:</b>", body_style), Paragraph(student_info['student_id'], body_bold)
        ],
        [
            Paragraph("<b>Grade/Class:</b>", body_style), Paragraph(student_info['grade_level'], body_bold),
            Paragraph("<b>Email ID:</b>", body_style), Paragraph(student_info['email'], body_bold)
        ],
        [
            Paragraph("<b>Overall Average:</b>", body_style), Paragraph(f"{student_avg_score:.2f}%", body_bold),
            Paragraph("<b>Risk Status:</b>", body_style), Paragraph(f"<font color='{risk_color.hexval()}'><b>{risk_cat}</b></font>", body_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[110, 160, 110, 160])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('LINEBELOW', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Subject Performance Table Header
    story.append(Paragraph("Academic Subject Breakdown", section_title))
    
    subj_data = [[
        Paragraph("Subject", header_style),
        Paragraph("Score (%)", header_style),
        Paragraph("Grade", header_style),
        Paragraph("Attendance Rate (%)", header_style),
        Paragraph("Study Hours/Week", header_style)
    ]]
    
    for idx, row in performance_df.iterrows():
        subj_data.append([
            Paragraph(row['subject'], cell_style),
            Paragraph(f"{row['score']:.1f}", cell_style),
            Paragraph(get_grade(row['score']), cell_style),
            Paragraph(f"{row['attendance_rate']:.1f}%", cell_style),
            Paragraph(f"{row['study_hours_per_week']:.1f}", cell_style)
        ])
        
    subj_table = Table(subj_data, colWidths=[150, 90, 80, 120, 100])
    subj_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F3A60')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CCCCCC')),
        ('TOPPADDING', (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F8F9FA')])
    ]))
    story.append(subj_table)
    story.append(Spacer(1, 15))
    
    # Embed Performance Chart
    story.append(Paragraph("Performance Visualizer", section_title))
    story.append(Image(chart_path, width=480, height=210))
    story.append(Spacer(1, 15))
    
    # Remarks / Context Notes
    story.append(Paragraph("Teacher Evaluation & Action Plan", section_title))
    
    # Dynamic Remarks
    if student_avg_score >= 85 and student_avg_attendance >= 85:
        remarks = (
            f"Excellent work, {student_info['name']}! Your academic scores reflect dedication. "
            f"With {student_avg_attendance:.1f}% attendance and {student_total_study:.1f} hours of weekly self-study, "
            f"you have set a high benchmark. Maintain this level of commitment."
        )
    elif student_avg_score >= 70 and student_avg_attendance >= 75:
        remarks = (
            f"Good performance, {student_info['name']}. You have a solid grasp of your subjects. "
            f"Increasing your study hours from {student_total_study:.1f} hours/week to about 12-14 hours and maintaining "
            f"an attendance rate above 85% will help push your scores into the excellent bracket."
        )
    else:
        remarks = (
            f"Academic intervention is recommended for {student_info['name']}. "
            f"The current average score is {student_avg_score:.2f}% with {student_avg_attendance:.1f}% attendance. "
            f"A structured study schedule targeting foundational concepts, along with regular school attendance, "
            f"is critical. We suggest parental support of High priority and setting up a counselor meeting."
        )
        
    remarks_data = [
        [Paragraph(f"<b>Parental Involvement:</b> {parental_invol} | <b>Extracurriculars:</b> {extra_curr}", body_style)],
        [Paragraph(f"<b>Remarks:</b> {remarks}", body_style)]
    ]
    remarks_table = Table(remarks_data, colWidths=[540])
    remarks_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#F8F9FA')),
        ('PADDING', (0,0), (-1,-1), 10),
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(remarks_table)
    story.append(Spacer(1, 30))
    
    # Signature Section
    sig_data = [
        [Paragraph("____________________________<br/><b>Class Teacher</b>", body_style), 
         Paragraph("____________________________<br/><b>Principal</b>", body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[270, 270])
    sig_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ]))
    story.append(sig_table)
    
    # Build the document
    doc.build(story)
    
    # Cleanup chart image
    if os.path.exists(chart_path):
        try:
            os.remove(chart_path)
        except OSError:
            pass
            
    print(f"Report card generated successfully at: {file_path}")
