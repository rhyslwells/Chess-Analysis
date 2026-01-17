# ============================================================================
# FILE 10: src/components/probability.py
# ============================================================================
"""
Win probability component.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.predictor import ChessPredictor


def render(df, analyzer, stats):
    """Render win probability analysis."""
    if len(df) < 20:
        st.info("At least 20 games are required for win probability modelling.")
        return

    # Train model
    predictor = ChessPredictor()
    X, y = analyzer.prepare_ml_features()
    training_results = predictor.train(X, y)
    metrics = training_results['classification_metrics']

    # Win probability curves
    st.subheader("Win Probability Predictions")
    st.markdown(
        "Based on your historical games, this model predicts your probability of winning "
        "against opponents of different ratings. Use the controls below to explore different scenarios."
    )

    _render_probability_curves(predictor, stats)

    st.divider()

    # Model details
    _render_model_details(training_results, predictor, metrics)


def _render_probability_curves(predictor, stats):
    """Render interactive win probability curves."""
    current_rating = int(stats["current_elo"])
    avg_rating = int(stats["avg_user_rating"])

    st.markdown(
        f"""
        **Your Rating Context**

        - Current rating (most recent game): **{current_rating}**
        - Average rating over this period: **{avg_rating}**
        """
    )

    # Controls
    col1, col2 = st.columns(2)
    
    with col1:
        assumed_rating = st.number_input(
            "Your Rating (what-if scenario)",
            min_value=400,
            max_value=5000,
            value=current_rating,
            step=10,
            help="Explore predictions at different rating levels without retraining the model"
        )
    
    with col2:
        rating_range = st.slider(
            "Opponent Rating Range",
            min_value=100,
            max_value=4000,
            value=(assumed_rating - 200, assumed_rating + 200),
            step=25,
            help="Set the range of opponent ratings to display"
        )

    min_r, max_r = rating_range

    # Curves
    st.markdown("### Predicted Win Probability by Color")
    
    tab_white, tab_black = st.tabs(["Playing as White", "Playing as Black"])
    
    with tab_white:
        st.caption("Your expected win probability when playing with white pieces")
        _render_curve(predictor, assumed_rating, True, min_r, max_r)
    
    with tab_black:
        st.caption("Your expected win probability when playing with black pieces")
        _render_curve(predictor, assumed_rating, False, min_r, max_r)


def _render_curve(predictor, assumed_rating, is_white, min_r, max_r):
    """Render a single probability curve."""
    curve = predictor.get_win_probability_curve(assumed_rating, is_white=is_white)
    curve = curve[(curve["opponent_rating"] >= min_r) & (curve["opponent_rating"] <= max_r)]

    fig = px.line(
        curve,
        x="opponent_rating",
        y="win_probability",
        labels={
            "opponent_rating": "Opponent Rating",
            "win_probability": "Win Probability",
        },
    )
    fig.add_hline(
        y=0.5, 
        line_dash="dash", 
        line_color="gray", 
        annotation_text="50% (Even odds)"
    )
    fig.update_layout(yaxis_tickformat=".0%")
    st.plotly_chart(fig, width='stretch')


def _render_model_details(training_results, predictor, metrics):
    """Render model performance details."""
    with st.expander("View Model Training & Performance Details", expanded=False):
        st.markdown(
            "This section provides detailed information about how the prediction model was trained "
            "and how accurate its predictions are. These metrics help you understand the reliability "
            "of the win probability predictions shown above."
        )
        
        st.markdown("---")
        
        # Training info
        st.markdown("### Training Information")
        st.markdown(
            "A **logistic regression** model was trained on your historical games to predict win probability "
            "based on your rating, opponent rating, rating difference, and piece color (white/black). "
            "The data was split into training data (80%) to teach the model patterns, and test data (20%) "
            "to evaluate how well it predicts outcomes on games it hasn't seen before."
        )
        
        info_col1, info_col2 = st.columns(2)
        info_col1.metric("Training Samples", training_results['n_train_samples'])
        info_col2.metric("Test Samples", training_results['n_test_samples'])
        
        st.markdown("---")
        
        # Confusion matrix
        _render_confusion_matrix(metrics)
        
        # Per-class metrics
        _render_class_metrics(metrics)
        
        # Overall metrics
        _render_overall_metrics(metrics)
        
        st.markdown("---")
        
        # Feature importance
        _render_feature_importance(predictor)


def _render_confusion_matrix(metrics):
    """Render confusion matrix."""
    st.markdown("### Confusion Matrix")
    st.caption(
        "The confusion matrix shows how the model's predictions compare to actual outcomes. "
        "Each cell shows the number of games in that category. Diagonal cells (top-left and bottom-right) "
        "represent correct predictions, while off-diagonal cells show prediction errors."
    )
    
    cm = metrics['confusion_matrix']
    cm_matrix = np.array([
        [cm['true_negatives'], cm['false_positives']],
        [cm['false_negatives'], cm['true_positives']]
    ])
    
    fig_cm = go.Figure(data=go.Heatmap(
        z=cm_matrix,
        x=['Predicted Loss/Draw', 'Predicted Win'],
        y=['Actual Loss/Draw', 'Actual Win'],
        text=cm_matrix,
        texttemplate='%{text}',
        textfont={"size": 16},
        colorscale='Blues',
        showscale=False
    ))
    
    fig_cm.update_layout(
        title="Confusion Matrix Visualization",
        xaxis_title="Predicted Class",
        yaxis_title="Actual Class",
        height=400
    )
    
    st.plotly_chart(fig_cm, width='stretch')


def _render_class_metrics(metrics):
    """Render per-class metrics."""
    st.markdown("### Per-Class Metrics")
    st.caption(
        "These metrics break down the model's performance for each outcome type. "
        "They show how well the model performs specifically for wins vs losses/draws."
    )
    
    class_report = metrics['classification_report']
    report_df = pd.DataFrame({
        'Class': ['Loss/Draw', 'Win'],
        'Precision': [
            class_report['0']['precision'],
            class_report['1']['precision']
        ],
        'Recall': [
            class_report['0']['recall'],
            class_report['1']['recall']
        ],
        'F1-Score': [
            class_report['0']['f1-score'],
            class_report['1']['f1-score']
        ],
        'Support': [
            class_report['0']['support'],
            class_report['1']['support']
        ]
    })
    
    st.dataframe(
        report_df.style.format({
            'Precision': '{:.1%}',
            'Recall': '{:.1%}',
            'F1-Score': '{:.1%}',
            'Support': '{:.0f}'
        }),
        hide_index=True,
        width='stretch'
    )
    
    with st.expander("Understanding These Metrics", expanded=False):
        st.markdown("""
        **Why are these different from overall accuracy?**
        
        Overall accuracy tells you what percentage of all predictions were correct, but it doesn't 
        tell you *which types* of predictions the model is good at. Per-class metrics reveal this detail.
        
        For example, you might have 70% overall accuracy, but the model could be:
        - Great at predicting wins (90% precision) but poor at predicting losses (50% precision), or
        - Balanced across both outcome types (70% for each)
        
        **Metric Definitions:**
        
        - **Precision**: When the model predicts this outcome, how often is it correct?  
          *High precision = few false alarms for this outcome type*
        
        - **Recall**: Of all actual occurrences of this outcome, how many does the model catch?  
          *High recall = few missed predictions for this outcome type*
        
        - **F1-Score**: Balance between precision and recall (harmonic mean)  
          *High F1 = good at both catching this outcome and avoiding false predictions*
        
        - **Support**: The number of test games with this actual outcome  
          *Shows how many examples the model had to evaluate*
        """)
        
        st.info(
            "**Tip**: A good model has similar, high metrics for both classes. "
            "If one class has much lower scores, the model struggles more with that outcome type."
        )


def _render_overall_metrics(metrics):
    """Render overall model metrics."""
    st.markdown("### Overall Model Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "Accuracy", 
        f"{metrics['accuracy']:.1%}",
        help="Percentage of all predictions (wins and losses/draws) that were correct"
    )
    col2.metric(
        "Precision", 
        f"{metrics['precision']:.1%}",
        help="When predicting a win, how often the model is correct (fewer false alarms)"
    )
    col3.metric(
        "Recall", 
        f"{metrics['recall']:.1%}",
        help="Of all actual wins, what percentage the model successfully identifies (fewer missed wins)"
    )
    col4.metric(
        "F1 Score", 
        f"{metrics['f1_score']:.1%}",
        help="Balanced measure combining precision and recall (harmonic mean)"
    )
    if metrics['roc_auc'] is not None:
        col5.metric(
            "ROC AUC", 
            f"{metrics['roc_auc']:.3f}",
            help="Model's ability to distinguish between wins and losses (0.5 = random, 1.0 = perfect)"
        )


def _render_feature_importance(predictor):
    """Render feature importance chart."""
    st.markdown("### Feature Importance")
    st.caption(
        "These coefficients show how each factor influences your win probability. "
        "Positive values increase win probability, negative values decrease it."
    )
    
    importance_df = predictor.get_feature_importance()
    if importance_df is not None:
        fig_importance = px.bar(
            importance_df,
            y='feature',
            x='coefficient',
            orientation='h',
            labels={'coefficient': 'Coefficient', 'feature': 'Feature'},
            title='Model Feature Coefficients',
            color='coefficient',
            color_continuous_scale='RdBu_r'
        )
        fig_importance.update_traces(
            hovertemplate='<b>%{y}</b><br>Coefficient: %{x:.3f}<extra></extra>'
        )
        fig_importance.update_layout(showlegend=False)
        st.plotly_chart(fig_importance, width='stretch')
    
    with st.expander("Understanding Feature Importance"):
        st.markdown("""
        **What do these coefficients mean?**
        
        - **Positive coefficient**: This factor increases your win probability
        - **Negative coefficient**: This factor decreases your win probability
        - **Larger magnitude**: Stronger influence on the outcome
        
        For example:
        - A positive coefficient for `is_white` means playing white gives you an advantage
        - A positive coefficient for `rating_diff` means higher rating differences favor you
        - The `user_rating` and `opponent_rating` coefficients show how raw ratings influence outcomes
        """)
