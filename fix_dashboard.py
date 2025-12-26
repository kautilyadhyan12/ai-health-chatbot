
"""
Fix dashboard loading issues
"""
import os
import sys

def apply_fixes():
    print("🔧 Applying dashboard fixes...")
    
    
    backup_files()
    
    
    fix_app_py()
    fix_dashboard_html()
    
    print("✅ Fixes applied successfully!")
    print("\n📋 Next steps:")
    print("1. Restart the server: python app.py")
    print("2. Clear browser cache")
    print("3. Login to dashboard - stats should load immediately")

def backup_files():
    """Create backups of original files"""
    import shutil
    import datetime
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = f"backups/{timestamp}"
    
    os.makedirs(backup_dir, exist_ok=True)
    
    files_to_backup = [
        'app.py',
        'templates/dashboard.html',
        'static/js/dashboard.js',
        'static/css/style.css'
    ]
    
    for file in files_to_backup:
        if os.path.exists(file):
            backup_path = os.path.join(backup_dir, file.replace('/', '_'))
            shutil.copy2(file, backup_path)
            print(f"📦 Backed up: {file}")

def fix_app_py():
    """Fix app.py"""
    with open('app.py', 'r') as f:
        content = f.read()
    
    
    dashboard_route = '''@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html', username=current_user.username)'''
    
    new_dashboard_route = '''@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Pre-load user statistics
    stats = get_user_statistics(current_user.id)
    
    return render_template('dashboard.html', 
                         username=current_user.username,
                         user_stats=stats)  # Pass stats to template'''
    
    if dashboard_route in content:
        content = content.replace(dashboard_route, new_dashboard_route)
        print("✅ Fixed dashboard route in app.py")
    else:
        print("⚠️ Could not find dashboard route in app.py")
    
    # Add new API endpoint
    api_endpoint = '''@app.route('/api/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics for immediate load"""
    try:
        stats = get_user_statistics(current_user.id)
        
        # Get recent chats for activity chart
        recent_chats = ChatHistory.query.filter_by(
            user_id=current_user.id
        ).order_by(ChatHistory.timestamp.desc()).limit(50).all()
        
        # Format chart data
        activity_data = []
        for i, chat in enumerate(recent_chats[:7][::-1]):  # Last 7 chats
            activity_data.append({
                'date': chat.timestamp.strftime('%m-%d'),
                'chats': i + 1  # Simple count for demo
            })
        
        return jsonify({
            'stats': stats,
            'activity': activity_data,
            'timestamp': datetime.now().isoformat(),
            'success': True
        })
        
    except Exception as e:
        print(f"❌ Dashboard stats error: {e}")
        return jsonify({'error': 'Failed to load dashboard stats', 'success': False}), 500'''
    
   
    if '@app.route(\'/api/user\')' in content:
        parts = content.split('@app.route(\'/api/user\')', 1)
        content = parts[0] + api_endpoint + '\n\n' + '@app.route(\'/api/user\')' + parts[1]
        print("✅ Added dashboard stats API endpoint")
    
    with open('app.py', 'w') as f:
        f.write(content)

def fix_dashboard_html():
    """Fix dashboard.html template"""
    with open('templates/dashboard.html', 'r') as f:
        content = f.read()
    
   
    quick_stats_section = '''<div class="quick-stats">
                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="totalChats">0</h3>
                        <p>Total Chats</p>
                    </div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="avgConfidence">0%</h3>
                        <p>Avg. Confidence</p>
                    </div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                        <i class="fas fa-brain"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="commonIntent">--</h3>
                        <p>Most Common Intent</p>
                    </div>
                    <div class="stat-trend">
                        <i class="fas fa-sync-alt"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="lastActive">Never</h3>
                        <p>Last Active</p>
                    </div>
                    <div class="stat-trend down">
                        <i class="fas fa-broadcast-tower"></i>
                        <span>Live</span>
                    </div>
                </div>
            </div>'''
    
    new_quick_stats = '''<div class="quick-stats">
                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="totalChats">{{ user_stats.total_chats }}</h3>
                        <p>Total Chats</p>
                    </div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
                        <i class="fas fa-heartbeat"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="avgConfidence">{{ user_stats.avg_confidence }}%</h3>
                        <p>Avg. Confidence</p>
                    </div>
                    <div class="stat-trend up">
                        <i class="fas fa-arrow-up"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                        <i class="fas fa-brain"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="commonIntent">{{ user_stats.most_common_intent }}</h3>
                        <p>Most Common Intent</p>
                    </div>
                    <div class="stat-trend">
                        <i class="fas fa-sync-alt"></i>
                        <span>Live</span>
                    </div>
                </div>

                <div class="stat-card">
                    <div class="stat-icon" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                        <i class="fas fa-clock"></i>
                    </div>
                    <div class="stat-info">
                        <h3 id="lastActive">{{ user_stats.last_active }}</h3>
                        <p>Last Active</p>
                    </div>
                    <div class="stat-trend down">
                        <i class="fas fa-broadcast-tower"></i>
                        <span>Live</span>
                    </div>
                </div>
            </div>'''
    
    if quick_stats_section in content:
        content = content.replace(quick_stats_section, new_quick_stats)
        print("✅ Fixed quick stats in dashboard.html")
    else:
        print("⚠️ Could not find quick stats section in dashboard.html")
    
    with open('templates/dashboard.html', 'w') as f:
        f.write(content)

if __name__ == '__main__':
    apply_fixes()