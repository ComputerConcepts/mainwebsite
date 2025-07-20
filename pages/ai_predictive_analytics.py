"""
AI-Powered Predictive Analytics and Business Insights Engine
Provides predictive analytics, trend analysis, and business intelligence
"""

import os
import json
from typing import Dict, List, Tuple, Optional
from collections import defaultdict, Counter
from datetime import datetime, timedelta
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import io
import base64


class PredictiveAnalyticsEngine:
    """AI-powered predictive analytics for business insights"""
    
    def __init__(self):
        self.models = {}
        self.predictions_history = []
        self.trend_data = {}
        self.alert_thresholds = {}
        
    def analyze_file_usage_patterns(self, file_activities: List[Dict]) -> Dict:
        """Analyze file usage patterns and predict future trends"""
        if not file_activities:
            return {'error': 'No file activity data available'}
        
        analysis = {
            'usage_trends': {},
            'predictions': {},
            'insights': [],
            'recommendations': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Analyze daily usage patterns
        daily_usage = self._calculate_daily_usage(file_activities)
        analysis['usage_trends']['daily_pattern'] = daily_usage
        
        # Analyze file type trends
        file_type_trends = self._analyze_file_type_trends(file_activities)
        analysis['usage_trends']['file_types'] = file_type_trends
        
        # Predict future usage
        usage_prediction = self._predict_usage_trends(daily_usage)
        analysis['predictions']['usage_forecast'] = usage_prediction
        
        # Generate insights
        insights = self._generate_usage_insights(daily_usage, file_type_trends)
        analysis['insights'] = insights
        
        # Generate recommendations
        recommendations = self._generate_usage_recommendations(analysis)
        analysis['recommendations'] = recommendations
        
        return analysis
    
    def predict_storage_requirements(self, current_usage: Dict, historical_data: List[Dict]) -> Dict:
        """Predict future storage requirements"""
        prediction = {
            'current_usage': current_usage,
            'predictions': {},
            'capacity_planning': {},
            'alerts': [],
            'generated_at': datetime.now().isoformat()
        }
        
        if not historical_data:
            # Simple prediction based on current usage
            current_used = current_usage.get('used_gb', 0)
            current_quota = current_usage.get('quota_gb', 10)
            
            # Assume 20% monthly growth
            monthly_growth = current_used * 0.2
            
            prediction['predictions'] = {
                '1_month': current_used + monthly_growth,
                '3_months': current_used + (monthly_growth * 3),
                '6_months': current_used + (monthly_growth * 6),
                '12_months': current_used + (monthly_growth * 12)
            }
        else:
            # Use historical data for more accurate prediction
            prediction['predictions'] = self._calculate_storage_prediction(historical_data)
        
        # Capacity planning
        prediction['capacity_planning'] = self._generate_capacity_plan(prediction['predictions'], current_usage.get('quota_gb', 10))
        
        # Generate alerts
        prediction['alerts'] = self._generate_storage_alerts(prediction['predictions'], current_usage)
        
        return prediction
    
    def analyze_productivity_patterns(self, user_activities: List[Dict]) -> Dict:
        """Analyze user productivity patterns"""
        analysis = {
            'productivity_metrics': {},
            'peak_hours': [],
            'efficiency_score': 0,
            'trends': {},
            'recommendations': [],
            'generated_at': datetime.now().isoformat()
        }
        
        if not user_activities:
            return analysis
        
        # Analyze hourly productivity
        hourly_activity = self._analyze_hourly_activity(user_activities)
        analysis['peak_hours'] = self._identify_peak_hours(hourly_activity)
        
        # Calculate productivity metrics
        analysis['productivity_metrics'] = self._calculate_productivity_metrics(user_activities)
        
        # Calculate efficiency score
        analysis['efficiency_score'] = self._calculate_efficiency_score(user_activities)
        
        # Analyze trends
        analysis['trends'] = self._analyze_productivity_trends(user_activities)
        
        # Generate recommendations
        analysis['recommendations'] = self._generate_productivity_recommendations(analysis)
        
        return analysis
    
    def detect_anomalies(self, data: List[Dict], metric: str) -> Dict:
        """Detect anomalies in data patterns"""
        anomaly_detection = {
            'anomalies_found': [],
            'anomaly_score': 0,
            'threshold_breaches': [],
            'analysis_summary': {},
            'generated_at': datetime.now().isoformat()
        }
        
        if not data or len(data) < 5:
            return anomaly_detection
        
        # Extract metric values
        values = []
        timestamps = []
        
        for item in data:
            if metric in item and 'timestamp' in item:
                values.append(float(item[metric]))
                timestamps.append(item['timestamp'])
        
        if len(values) < 5:
            return anomaly_detection
        
        # Calculate statistical measures
        mean_value = np.mean(values)
        std_value = np.std(values)
        
        # Define anomaly threshold (2 standard deviations)
        upper_threshold = mean_value + (2 * std_value)
        lower_threshold = mean_value - (2 * std_value)
        
        # Detect anomalies
        anomalies = []
        for i, (value, timestamp) in enumerate(zip(values, timestamps)):
            if value > upper_threshold or value < lower_threshold:
                anomalies.append({
                    'index': i,
                    'value': value,
                    'timestamp': timestamp,
                    'deviation': abs(value - mean_value) / std_value,
                    'type': 'high' if value > upper_threshold else 'low'
                })
        
        anomaly_detection['anomalies_found'] = anomalies
        anomaly_detection['anomaly_score'] = len(anomalies) / len(values) * 100
        
        # Analysis summary
        anomaly_detection['analysis_summary'] = {
            'total_data_points': len(values),
            'anomalies_count': len(anomalies),
            'mean_value': round(mean_value, 2),
            'std_deviation': round(std_value, 2),
            'upper_threshold': round(upper_threshold, 2),
            'lower_threshold': round(lower_threshold, 2)
        }
        
        return anomaly_detection
    
    def forecast_business_metrics(self, historical_metrics: Dict) -> Dict:
        """Forecast business metrics using trend analysis"""
        forecast = {
            'forecasts': {},
            'confidence_intervals': {},
            'trend_analysis': {},
            'business_insights': [],
            'generated_at': datetime.now().isoformat()
        }
        
        for metric_name, metric_data in historical_metrics.items():
            if len(metric_data) >= 3:  # Need at least 3 data points
                metric_forecast = self._forecast_metric(metric_name, metric_data)
                forecast['forecasts'][metric_name] = metric_forecast
                
                # Analyze trend
                trend = self._analyze_metric_trend(metric_data)
                forecast['trend_analysis'][metric_name] = trend
        
        # Generate business insights
        forecast['business_insights'] = self._generate_business_insights(forecast)
        
        return forecast
    
    def analyze_collaboration_patterns(self, collaboration_data: List[Dict]) -> Dict:
        """Analyze collaboration patterns and team dynamics"""
        analysis = {
            'collaboration_metrics': {},
            'network_analysis': {},
            'team_insights': [],
            'optimization_suggestions': [],
            'generated_at': datetime.now().isoformat()
        }
        
        if not collaboration_data:
            return analysis
        
        # Analyze sharing patterns
        sharing_patterns = self._analyze_sharing_patterns(collaboration_data)
        analysis['collaboration_metrics']['sharing'] = sharing_patterns
        
        # Network analysis
        network_metrics = self._analyze_collaboration_network(collaboration_data)
        analysis['network_analysis'] = network_metrics
        
        # Generate team insights
        analysis['team_insights'] = self._generate_team_insights(sharing_patterns, network_metrics)
        
        # Optimization suggestions
        analysis['optimization_suggestions'] = self._generate_collaboration_suggestions(analysis)
        
        return analysis
    
    def risk_assessment(self, project_data: Dict, historical_risks: List[Dict]) -> Dict:
        """Assess project risks using AI analysis"""
        assessment = {
            'risk_score': 0,
            'risk_factors': [],
            'mitigation_strategies': [],
            'probability_analysis': {},
            'impact_analysis': {},
            'recommendations': [],
            'generated_at': datetime.now().isoformat()
        }
        
        # Analyze current project factors
        risk_factors = self._identify_risk_factors(project_data)
        assessment['risk_factors'] = risk_factors
        
        # Calculate overall risk score
        assessment['risk_score'] = self._calculate_risk_score(risk_factors)
        
        # Probability analysis based on historical data
        assessment['probability_analysis'] = self._analyze_risk_probability(risk_factors, historical_risks)
        
        # Impact analysis
        assessment['impact_analysis'] = self._analyze_risk_impact(risk_factors, project_data)
        
        # Generate mitigation strategies
        assessment['mitigation_strategies'] = self._generate_mitigation_strategies(risk_factors)
        
        # Generate recommendations
        assessment['recommendations'] = self._generate_risk_recommendations(assessment)
        
        return assessment
    
    def _calculate_daily_usage(self, activities: List[Dict]) -> Dict:
        """Calculate daily usage patterns"""
        daily_counts = defaultdict(int)
        daily_files = defaultdict(set)
        
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    date = datetime.fromisoformat(activity['timestamp']).date()
                    daily_counts[str(date)] += 1
                    if 'filename' in activity:
                        daily_files[str(date)].add(activity['filename'])
                except:
                    continue
        
        return {
            'daily_activity_counts': dict(daily_counts),
            'daily_unique_files': {date: len(files) for date, files in daily_files.items()},
            'average_daily_activity': sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        }
    
    def _analyze_file_type_trends(self, activities: List[Dict]) -> Dict:
        """Analyze file type usage trends"""
        file_type_counts = defaultdict(int)
        file_type_by_date = defaultdict(lambda: defaultdict(int))
        
        for activity in activities:
            filename = activity.get('filename', '')
            if filename and '.' in filename:
                file_ext = filename.split('.')[-1].lower()
                file_type_counts[file_ext] += 1
                
                if 'timestamp' in activity:
                    try:
                        date = datetime.fromisoformat(activity['timestamp']).date()
                        file_type_by_date[str(date)][file_ext] += 1
                    except:
                        continue
        
        # Calculate growth rates
        growth_rates = {}
        for file_type in file_type_counts:
            dates = sorted(file_type_by_date.keys())
            if len(dates) >= 2:
                first_week = sum(file_type_by_date[date][file_type] for date in dates[:7])
                last_week = sum(file_type_by_date[date][file_type] for date in dates[-7:])
                if first_week > 0:
                    growth_rates[file_type] = ((last_week - first_week) / first_week) * 100
        
        return {
            'total_counts': dict(file_type_counts),
            'growth_rates': growth_rates,
            'trending_types': sorted(growth_rates.items(), key=lambda x: x[1], reverse=True)[:5]
        }
    
    def _predict_usage_trends(self, daily_usage: Dict) -> Dict:
        """Predict future usage trends"""
        activity_counts = daily_usage.get('daily_activity_counts', {})
        
        if len(activity_counts) < 3:
            return {'prediction': 'Insufficient data for prediction'}
        
        # Prepare data for linear regression
        dates = sorted(activity_counts.keys())
        values = [activity_counts[date] for date in dates]
        
        # Create numerical date representation
        X = np.array(range(len(dates))).reshape(-1, 1)
        y = np.array(values)
        
        # Fit linear regression model
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict next 7 days
        future_X = np.array(range(len(dates), len(dates) + 7)).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        # Calculate trend
        trend_slope = model.coef_[0]
        trend_direction = 'increasing' if trend_slope > 0 else 'decreasing' if trend_slope < 0 else 'stable'
        
        return {
            'next_7_days': [max(0, int(p)) for p in predictions],
            'trend_direction': trend_direction,
            'trend_strength': abs(trend_slope),
            'confidence': 'medium' if len(dates) > 7 else 'low'
        }
    
    def _generate_usage_insights(self, daily_usage: Dict, file_type_trends: Dict) -> List[str]:
        """Generate insights from usage analysis"""
        insights = []
        
        # Daily usage insights
        avg_activity = daily_usage.get('average_daily_activity', 0)
        if avg_activity > 20:
            insights.append(f"High activity user with {avg_activity:.1f} daily actions on average")
        elif avg_activity > 10:
            insights.append(f"Moderate activity user with {avg_activity:.1f} daily actions on average")
        else:
            insights.append(f"Light activity user with {avg_activity:.1f} daily actions on average")
        
        # File type insights
        trending_types = file_type_trends.get('trending_types', [])
        if trending_types:
            top_trending = trending_types[0]
            insights.append(f"Most growing file type: {top_trending[0]} with {top_trending[1]:.1f}% growth")
        
        total_counts = file_type_trends.get('total_counts', {})
        if total_counts:
            most_used = max(total_counts, key=total_counts.get)
            insights.append(f"Most frequently used file type: {most_used} ({total_counts[most_used]} files)")
        
        return insights
    
    def _generate_usage_recommendations(self, analysis: Dict) -> List[str]:
        """Generate usage optimization recommendations"""
        recommendations = []
        
        insights = analysis.get('insights', [])
        predictions = analysis.get('predictions', {})
        
        # Based on activity level
        if 'High activity user' in str(insights):
            recommendations.append("Consider using automation tools to streamline repetitive tasks")
            recommendations.append("Set up keyboard shortcuts for frequently used actions")
        elif 'Light activity user' in str(insights):
            recommendations.append("Explore additional features that might enhance your workflow")
        
        # Based on trend predictions
        usage_forecast = predictions.get('usage_forecast', {})
        if usage_forecast.get('trend_direction') == 'increasing':
            recommendations.append("Usage is trending upward - consider organizing files proactively")
        
        # Based on file types
        file_types = analysis.get('usage_trends', {}).get('file_types', {})
        trending_types = file_types.get('trending_types', [])
        if trending_types:
            top_type = trending_types[0][0]
            recommendations.append(f"Create dedicated folders for {top_type} files to improve organization")
        
        return recommendations
    
    def _calculate_storage_prediction(self, historical_data: List[Dict]) -> Dict:
        """Calculate storage usage prediction based on historical data"""
        if len(historical_data) < 2:
            return {'error': 'Insufficient historical data'}
        
        # Extract storage values and dates
        dates = []
        usage_values = []
        
        for data in historical_data:
            if 'date' in data and 'used_gb' in data:
                dates.append(data['date'])
                usage_values.append(data['used_gb'])
        
        if len(usage_values) < 2:
            return {'error': 'Insufficient usage data'}
        
        # Simple linear trend calculation
        X = np.array(range(len(usage_values))).reshape(-1, 1)
        y = np.array(usage_values)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Predict future values
        future_periods = [30, 90, 180, 365]  # 1, 3, 6, 12 months in days
        current_period = len(usage_values)
        
        predictions = {}
        for days in future_periods:
            future_X = np.array([[current_period + (days / 30)]])  # Convert to monthly periods
            predicted_usage = model.predict(future_X)[0]
            
            period_name = f"{days // 30}_months" if days >= 30 else f"{days}_days"
            predictions[period_name] = max(0, predicted_usage)  # Ensure non-negative
        
        return predictions
    
    def _generate_capacity_plan(self, predictions: Dict, current_quota: float) -> Dict:
        """Generate capacity planning recommendations"""
        plan = {
            'quota_recommendations': {},
            'timeline_alerts': [],
            'expansion_needed': False
        }
        
        for period, predicted_usage in predictions.items():
            utilization = (predicted_usage / current_quota) * 100
            
            if utilization > 90:
                plan['quota_recommendations'][period] = {
                    'recommended_quota': predicted_usage * 1.2,  # 20% buffer
                    'utilization': utilization,
                    'action': 'Immediate expansion needed'
                }
                plan['expansion_needed'] = True
            elif utilization > 75:
                plan['quota_recommendations'][period] = {
                    'recommended_quota': predicted_usage * 1.1,  # 10% buffer
                    'utilization': utilization,
                    'action': 'Plan for expansion'
                }
            else:
                plan['quota_recommendations'][period] = {
                    'recommended_quota': current_quota,
                    'utilization': utilization,
                    'action': 'Current quota sufficient'
                }
        
        return plan
    
    def _generate_storage_alerts(self, predictions: Dict, current_usage: Dict) -> List[Dict]:
        """Generate storage-related alerts"""
        alerts = []
        current_used = current_usage.get('used_gb', 0)
        current_quota = current_usage.get('quota_gb', 10)
        current_utilization = (current_used / current_quota) * 100
        
        # Current usage alerts
        if current_utilization > 90:
            alerts.append({
                'type': 'critical',
                'message': f'Storage {current_utilization:.1f}% full - immediate action required',
                'priority': 'high'
            })
        elif current_utilization > 75:
            alerts.append({
                'type': 'warning',
                'message': f'Storage {current_utilization:.1f}% full - monitor usage',
                'priority': 'medium'
            })
        
        # Future usage alerts
        for period, predicted_usage in predictions.items():
            predicted_utilization = (predicted_usage / current_quota) * 100
            if predicted_utilization > 90:
                alerts.append({
                    'type': 'prediction',
                    'message': f'Storage expected to be {predicted_utilization:.1f}% full in {period}',
                    'priority': 'medium'
                })
        
        return alerts
    
    def _analyze_hourly_activity(self, activities: List[Dict]) -> Dict:
        """Analyze activity patterns by hour"""
        hourly_counts = defaultdict(int)
        
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    hour = datetime.fromisoformat(activity['timestamp']).hour
                    hourly_counts[hour] += 1
                except:
                    continue
        
        return dict(hourly_counts)
    
    def _identify_peak_hours(self, hourly_activity: Dict) -> List[Dict]:
        """Identify peak productivity hours"""
        if not hourly_activity:
            return []
        
        # Sort hours by activity count
        sorted_hours = sorted(hourly_activity.items(), key=lambda x: x[1], reverse=True)
        
        peak_hours = []
        for hour, count in sorted_hours[:3]:  # Top 3 hours
            peak_hours.append({
                'hour': hour,
                'activity_count': count,
                'time_range': f"{hour:02d}:00-{(hour+1)%24:02d}:00"
            })
        
        return peak_hours
    
    def _calculate_productivity_metrics(self, activities: List[Dict]) -> Dict:
        """Calculate productivity metrics"""
        if not activities:
            return {}
        
        # Calculate various metrics
        total_activities = len(activities)
        
        # Activities per day
        dates = set()
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    date = datetime.fromisoformat(activity['timestamp']).date()
                    dates.add(date)
                except:
                    continue
        
        activities_per_day = total_activities / len(dates) if dates else 0
        
        # File creation vs modification ratio
        creation_activities = sum(1 for activity in activities if activity.get('action') == 'create')
        modification_activities = sum(1 for activity in activities if activity.get('action') == 'modify')
        
        return {
            'total_activities': total_activities,
            'activities_per_day': round(activities_per_day, 1),
            'active_days': len(dates),
            'creation_ratio': (creation_activities / total_activities * 100) if total_activities > 0 else 0,
            'modification_ratio': (modification_activities / total_activities * 100) if total_activities > 0 else 0
        }
    
    def _calculate_efficiency_score(self, activities: List[Dict]) -> float:
        """Calculate overall efficiency score (0-100)"""
        if not activities:
            return 0
        
        score = 0
        factors = 0
        
        # Factor 1: Activity consistency (regular daily usage)
        dates = set()
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    date = datetime.fromisoformat(activity['timestamp']).date()
                    dates.add(date)
                except:
                    continue
        
        if dates:
            date_range = (max(dates) - min(dates)).days + 1
            consistency = len(dates) / date_range if date_range > 0 else 1
            score += consistency * 30
            factors += 30
        
        # Factor 2: Productive hours usage (working during business hours)
        business_hour_activities = 0
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    hour = datetime.fromisoformat(activity['timestamp']).hour
                    if 9 <= hour <= 17:  # Business hours
                        business_hour_activities += 1
                except:
                    continue
        
        business_hour_ratio = business_hour_activities / len(activities)
        score += business_hour_ratio * 25
        factors += 25
        
        # Factor 3: File organization (varied file types indicate diverse work)
        file_types = set()
        for activity in activities:
            filename = activity.get('filename', '')
            if filename and '.' in filename:
                file_ext = filename.split('.')[-1].lower()
                file_types.add(file_ext)
        
        type_diversity = min(len(file_types) / 5, 1)  # Normalize to max 5 types
        score += type_diversity * 25
        factors += 25
        
        # Factor 4: Activity volume (appropriate amount of daily activity)
        total_activities = len(activities)
        days_active = len(dates) if dates else 1
        avg_daily_activity = total_activities / days_active
        
        # Optimal range is 10-30 activities per day
        if 10 <= avg_daily_activity <= 30:
            volume_score = 1.0
        elif avg_daily_activity < 10:
            volume_score = avg_daily_activity / 10
        else:
            volume_score = max(0, 1 - (avg_daily_activity - 30) / 50)
        
        score += volume_score * 20
        factors += 20
        
        return (score / factors * 100) if factors > 0 else 0
    
    def _analyze_productivity_trends(self, activities: List[Dict]) -> Dict:
        """Analyze productivity trends over time"""
        trends = {}
        
        # Group activities by week
        weekly_activity = defaultdict(int)
        for activity in activities:
            if 'timestamp' in activity:
                try:
                    date = datetime.fromisoformat(activity['timestamp']).date()
                    week = date.isocalendar()[:2]  # (year, week)
                    weekly_activity[week] += 1
                except:
                    continue
        
        if len(weekly_activity) >= 2:
            weeks = sorted(weekly_activity.keys())
            values = [weekly_activity[week] for week in weeks]
            
            # Calculate trend
            if len(values) >= 3:
                # Simple trend calculation
                recent_avg = sum(values[-3:]) / 3
                earlier_avg = sum(values[:3]) / 3
                
                trend_change = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
                
                trends['weekly_trend'] = {
                    'direction': 'increasing' if trend_change > 5 else 'decreasing' if trend_change < -5 else 'stable',
                    'change_percentage': round(trend_change, 1),
                    'recent_average': round(recent_avg, 1),
                    'baseline_average': round(earlier_avg, 1)
                }
        
        return trends
    
    def _generate_productivity_recommendations(self, analysis: Dict) -> List[str]:
        """Generate productivity improvement recommendations"""
        recommendations = []
        
        efficiency_score = analysis.get('efficiency_score', 0)
        peak_hours = analysis.get('peak_hours', [])
        trends = analysis.get('trends', {})
        
        # Efficiency-based recommendations
        if efficiency_score < 50:
            recommendations.append("Consider establishing more consistent daily work routines")
            recommendations.append("Focus on working during your most productive hours")
        elif efficiency_score > 80:
            recommendations.append("Excellent productivity patterns - maintain current habits")
        
        # Peak hours recommendations
        if peak_hours:
            top_hour = peak_hours[0]['hour']
            recommendations.append(f"Schedule important tasks around {top_hour:02d}:00 - your most active hour")
        
        # Trend-based recommendations
        weekly_trend = trends.get('weekly_trend', {})
        if weekly_trend.get('direction') == 'decreasing':
            recommendations.append("Activity has been decreasing - consider setting daily productivity goals")
        elif weekly_trend.get('direction') == 'increasing':
            recommendations.append("Great momentum! Your activity is trending upward")
        
        return recommendations
    
    def _forecast_metric(self, metric_name: str, metric_data: List) -> Dict:
        """Forecast a specific metric"""
        if len(metric_data) < 3:
            return {'error': 'Insufficient data'}
        
        # Simple linear regression forecast
        X = np.array(range(len(metric_data))).reshape(-1, 1)
        y = np.array(metric_data)
        
        model = LinearRegression()
        model.fit(X, y)
        
        # Forecast next 4 periods
        future_X = np.array(range(len(metric_data), len(metric_data) + 4)).reshape(-1, 1)
        predictions = model.predict(future_X)
        
        return {
            'next_4_periods': predictions.tolist(),
            'trend_slope': model.coef_[0],
            'confidence': 'medium' if len(metric_data) > 5 else 'low'
        }
    
    def _analyze_metric_trend(self, metric_data: List) -> Dict:
        """Analyze trend for a metric"""
        if len(metric_data) < 2:
            return {'trend': 'insufficient_data'}
        
        # Calculate simple trend
        first_half = metric_data[:len(metric_data)//2]
        second_half = metric_data[len(metric_data)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        change_percent = ((second_avg - first_avg) / first_avg * 100) if first_avg > 0 else 0
        
        if change_percent > 10:
            trend = 'strong_upward'
        elif change_percent > 2:
            trend = 'upward'
        elif change_percent < -10:
            trend = 'strong_downward'
        elif change_percent < -2:
            trend = 'downward'
        else:
            trend = 'stable'
        
        return {
            'trend': trend,
            'change_percent': round(change_percent, 1),
            'first_half_avg': round(first_avg, 2),
            'second_half_avg': round(second_avg, 2)
        }
    
    def _generate_business_insights(self, forecast: Dict) -> List[str]:
        """Generate business insights from forecasts"""
        insights = []
        
        forecasts = forecast.get('forecasts', {})
        trends = forecast.get('trend_analysis', {})
        
        # Analyze overall trends
        upward_trends = [name for name, trend in trends.items() if 'upward' in trend.get('trend', '')]
        downward_trends = [name for name, trend in trends.items() if 'downward' in trend.get('trend', '')]
        
        if upward_trends:
            insights.append(f"Growing metrics: {', '.join(upward_trends)}")
        
        if downward_trends:
            insights.append(f"Declining metrics: {', '.join(downward_trends)}")
        
        # Specific metric insights
        for metric_name, trend_data in trends.items():
            change_percent = trend_data.get('change_percent', 0)
            if abs(change_percent) > 20:
                direction = 'increased' if change_percent > 0 else 'decreased'
                insights.append(f"{metric_name} has {direction} by {abs(change_percent):.1f}%")
        
        return insights
    
    def _analyze_sharing_patterns(self, collaboration_data: List[Dict]) -> Dict:
        """Analyze file sharing patterns"""
        patterns = {
            'total_shares': len(collaboration_data),
            'unique_sharers': set(),
            'unique_recipients': set(),
            'file_types_shared': defaultdict(int),
            'sharing_frequency': defaultdict(int)
        }
        
        for share in collaboration_data:
            sharer = share.get('shared_by', '')
            recipient = share.get('shared_with', '')
            filename = share.get('filename', '')
            
            if sharer:
                patterns['unique_sharers'].add(sharer)
            if recipient:
                patterns['unique_recipients'].add(recipient)
            
            if filename and '.' in filename:
                file_ext = filename.split('.')[-1].lower()
                patterns['file_types_shared'][file_ext] += 1
            
            if 'timestamp' in share:
                try:
                    date = datetime.fromisoformat(share['timestamp']).date()
                    patterns['sharing_frequency'][str(date)] += 1
                except:
                    continue
        
        patterns['unique_sharers'] = len(patterns['unique_sharers'])
        patterns['unique_recipients'] = len(patterns['unique_recipients'])
        patterns['file_types_shared'] = dict(patterns['file_types_shared'])
        patterns['sharing_frequency'] = dict(patterns['sharing_frequency'])
        
        return patterns
    
    def _analyze_collaboration_network(self, collaboration_data: List[Dict]) -> Dict:
        """Analyze collaboration network structure"""
        network = {
            'connections': defaultdict(set),
            'centrality_scores': {},
            'collaboration_clusters': []
        }
        
        # Build connection graph
        for share in collaboration_data:
            sharer = share.get('shared_by', '')
            recipient = share.get('shared_with', '')
            
            if sharer and recipient:
                network['connections'][sharer].add(recipient)
                network['connections'][recipient].add(sharer)
        
        # Calculate simple centrality (number of connections)
        for person, connections in network['connections'].items():
            network['centrality_scores'][person] = len(connections)
        
        # Convert sets to lists for JSON serialization
        network['connections'] = {person: list(connections) for person, connections in network['connections'].items()}
        
        return network
    
    def _generate_team_insights(self, sharing_patterns: Dict, network_metrics: Dict) -> List[str]:
        """Generate team collaboration insights"""
        insights = []
        
        total_shares = sharing_patterns.get('total_shares', 0)
        unique_sharers = sharing_patterns.get('unique_sharers', 0)
        unique_recipients = sharing_patterns.get('unique_recipients', 0)
        
        if total_shares > 0:
            insights.append(f"Active collaboration with {total_shares} file shares")
            insights.append(f"Collaboration involves {unique_sharers} sharers and {unique_recipients} recipients")
        
        # Most shared file types
        file_types = sharing_patterns.get('file_types_shared', {})
        if file_types:
            most_shared_type = max(file_types, key=file_types.get)
            insights.append(f"Most shared file type: {most_shared_type} ({file_types[most_shared_type]} shares)")
        
        # Network insights
        centrality_scores = network_metrics.get('centrality_scores', {})
        if centrality_scores:
            most_connected = max(centrality_scores, key=centrality_scores.get)
            insights.append(f"Most connected team member: {most_connected} ({centrality_scores[most_connected]} connections)")
        
        return insights
    
    def _generate_collaboration_suggestions(self, analysis: Dict) -> List[str]:
        """Generate collaboration optimization suggestions"""
        suggestions = []
        
        team_insights = analysis.get('team_insights', [])
        collaboration_metrics = analysis.get('collaboration_metrics', {})
        
        sharing_patterns = collaboration_metrics.get('sharing', {})
        total_shares = sharing_patterns.get('total_shares', 0)
        
        if total_shares == 0:
            suggestions.append("Consider setting up shared folders for team collaboration")
        elif total_shares < 10:
            suggestions.append("Collaboration is light - explore more team sharing opportunities")
        else:
            suggestions.append("Good collaboration activity - maintain current sharing practices")
        
        # File type suggestions
        file_types = sharing_patterns.get('file_types_shared', {})
        if len(file_types) == 1:
            suggestions.append("Consider sharing diverse file types to enhance collaboration")
        
        return suggestions
    
    def _identify_risk_factors(self, project_data: Dict) -> List[Dict]:
        """Identify potential risk factors in project data"""
        risk_factors = []
        
        # Budget risk
        budget_used = project_data.get('budget_used_percent', 0)
        completion = project_data.get('completion_percent', 0)
        
        if budget_used > completion + 20:
            risk_factors.append({
                'type': 'budget_overrun',
                'severity': 'high',
                'description': f'Budget usage ({budget_used}%) exceeds completion ({completion}%)',
                'impact': 'financial'
            })
        
        # Schedule risk
        planned_duration = project_data.get('planned_duration_days', 0)
        elapsed_duration = project_data.get('elapsed_duration_days', 0)
        
        if planned_duration > 0 and elapsed_duration > planned_duration * 1.2:
            risk_factors.append({
                'type': 'schedule_delay',
                'severity': 'medium',
                'description': f'Project duration exceeded planned timeline by {((elapsed_duration/planned_duration - 1) * 100):.1f}%',
                'impact': 'timeline'
            })
        
        # Resource risk
        team_size = project_data.get('team_size', 0)
        if team_size < 3:
            risk_factors.append({
                'type': 'resource_constraint',
                'severity': 'medium',
                'description': 'Small team size may create dependencies and bottlenecks',
                'impact': 'delivery'
            })
        
        # Scope risk
        scope_changes = project_data.get('scope_changes', 0)
        if scope_changes > 3:
            risk_factors.append({
                'type': 'scope_creep',
                'severity': 'medium',
                'description': f'Multiple scope changes ({scope_changes}) detected',
                'impact': 'delivery'
            })
        
        return risk_factors
    
    def _calculate_risk_score(self, risk_factors: List[Dict]) -> float:
        """Calculate overall risk score (0-100)"""
        if not risk_factors:
            return 0
        
        severity_weights = {'low': 1, 'medium': 2, 'high': 3}
        total_score = 0
        
        for factor in risk_factors:
            severity = factor.get('severity', 'medium')
            weight = severity_weights.get(severity, 2)
            total_score += weight * 10  # Each factor contributes 10-30 points
        
        return min(100, total_score)
    
    def _analyze_risk_probability(self, risk_factors: List[Dict], historical_risks: List[Dict]) -> Dict:
        """Analyze probability of risks based on historical data"""
        probability_analysis = {}
        
        # Count historical occurrences of each risk type
        historical_counts = defaultdict(int)
        for risk in historical_risks:
            risk_type = risk.get('type', 'unknown')
            historical_counts[risk_type] += 1
        
        total_historical = len(historical_risks) if historical_risks else 1
        
        for factor in risk_factors:
            risk_type = factor.get('type', 'unknown')
            historical_count = historical_counts.get(risk_type, 0)
            
            # Calculate probability based on historical frequency
            probability = (historical_count / total_historical) * 100
            
            probability_analysis[risk_type] = {
                'probability_percent': round(probability, 1),
                'historical_occurrences': historical_count,
                'classification': 'high' if probability > 30 else 'medium' if probability > 10 else 'low'
            }
        
        return probability_analysis
    
    def _analyze_risk_impact(self, risk_factors: List[Dict], project_data: Dict) -> Dict:
        """Analyze potential impact of identified risks"""
        impact_analysis = {}
        
        project_value = project_data.get('project_value', 100000)  # Default value
        
        for factor in risk_factors:
            risk_type = factor.get('type', 'unknown')
            severity = factor.get('severity', 'medium')
            
            # Estimate impact based on risk type and severity
            impact_multipliers = {
                'budget_overrun': {'low': 0.05, 'medium': 0.15, 'high': 0.30},
                'schedule_delay': {'low': 0.03, 'medium': 0.10, 'high': 0.25},
                'resource_constraint': {'low': 0.02, 'medium': 0.08, 'high': 0.20},
                'scope_creep': {'low': 0.04, 'medium': 0.12, 'high': 0.25}
            }
            
            multiplier = impact_multipliers.get(risk_type, {}).get(severity, 0.10)
            estimated_impact = project_value * multiplier
            
            impact_analysis[risk_type] = {
                'estimated_cost_impact': round(estimated_impact, 2),
                'impact_percentage': round(multiplier * 100, 1),
                'severity': severity
            }
        
        return impact_analysis
    
    def _generate_mitigation_strategies(self, risk_factors: List[Dict]) -> List[Dict]:
        """Generate mitigation strategies for identified risks"""
        strategies = []
        
        strategy_templates = {
            'budget_overrun': {
                'strategy': 'Implement strict budget monitoring and approval processes',
                'actions': [
                    'Review budget weekly',
                    'Require approval for expenses over threshold',
                    'Identify cost reduction opportunities'
                ]
            },
            'schedule_delay': {
                'strategy': 'Accelerate critical path activities and improve resource allocation',
                'actions': [
                    'Fast-track critical activities',
                    'Add resources to bottleneck tasks',
                    'Re-evaluate scope and priorities'
                ]
            },
            'resource_constraint': {
                'strategy': 'Expand team capacity and cross-train team members',
                'actions': [
                    'Hire additional team members',
                    'Cross-train existing staff',
                    'Consider outsourcing non-critical tasks'
                ]
            },
            'scope_creep': {
                'strategy': 'Implement change control process',
                'actions': [
                    'Establish formal change approval process',
                    'Document all scope changes',
                    'Assess impact before approving changes'
                ]
            }
        }
        
        for factor in risk_factors:
            risk_type = factor.get('type', 'unknown')
            if risk_type in strategy_templates:
                strategy = strategy_templates[risk_type].copy()
                strategy['risk_type'] = risk_type
                strategy['priority'] = factor.get('severity', 'medium')
                strategies.append(strategy)
        
        return strategies
    
    def _generate_risk_recommendations(self, assessment: Dict) -> List[str]:
        """Generate overall risk management recommendations"""
        recommendations = []
        
        risk_score = assessment.get('risk_score', 0)
        risk_factors = assessment.get('risk_factors', [])
        
        # Overall risk level recommendations
        if risk_score > 70:
            recommendations.append("High risk project - implement immediate risk mitigation measures")
            recommendations.append("Consider escalating to senior management for additional support")
        elif risk_score > 40:
            recommendations.append("Moderate risk level - monitor closely and implement preventive measures")
        else:
            recommendations.append("Low risk project - maintain current monitoring practices")
        
        # Specific risk type recommendations
        high_severity_risks = [rf for rf in risk_factors if rf.get('severity') == 'high']
        if high_severity_risks:
            recommendations.append(f"Address {len(high_severity_risks)} high-severity risks immediately")
        
        # Prevention recommendations
        recommendations.append("Establish regular risk review meetings")
        recommendations.append("Update risk register weekly")
        
        return recommendations


def create_predictive_analytics_engine():
    """Factory function to create predictive analytics engine"""
    return PredictiveAnalyticsEngine()
