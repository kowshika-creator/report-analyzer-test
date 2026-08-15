import React, { useState } from 'react';
import {
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ScrollView,
  TextInput,
  ActivityIndicator,
  SafeAreaView,
  StatusBar,
  Alert,
  Dimensions,
  Platform
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import * as DocumentPicker from 'expo-document-picker';

// Update API_HOST to match your local IP or backend URL
const API_HOST = Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://localhost:8000';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard'); // 'dashboard' | 'chat'
  const [uploading, setUploading] = useState(false);
  const [reportData, setReportData] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('English');
  const [errorMessage, setErrorMessage] = useState(null);

  // Chat state
  const [selectedTone, setSelectedTone] = useState('Empathetic');
  const [chatMessages, setChatMessages] = useState([]);
  const [currentQuery, setCurrentQuery] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [chatDisclaimer, setChatDisclaimer] = useState('');

  // Pick Document / Image File
  const handlePickDocument = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: ['application/pdf', 'image/*'],
        copyToCacheDirectory: true
      });

      if (!result.canceled && result.assets && result.assets.length > 0) {
        const fileAsset = result.assets[0];
        await uploadReportFile(fileAsset.uri, fileAsset.name, fileAsset.mimeType || 'application/pdf');
      }
    } catch (err) {
      Alert.alert('Selection Error', 'Failed to select report file.');
    }
  };

  // Pick / Take Photo
  const handleTakePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Denied', 'Camera permissions are required to scan physical reports.');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.9
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      const photo = result.assets[0];
      await uploadReportFile(photo.uri, 'scanned_report.jpg', 'image/jpeg');
    }
  };

  // Upload to FastAPI Endpoint
  const uploadReportFile = async (fileUri, fileName, fileType) => {
    setUploading(true);
    setErrorMessage(null);

    const formData = new FormData();
    formData.append('file', {
      uri: Platform.OS === 'android' ? fileUri : fileUri.replace('file://', ''),
      name: fileName,
      type: fileType
    });
    formData.append('language', selectedLanguage);

    try {
      const response = await fetch(`${API_HOST}/api/analyze-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'multipart/form-data'
        },
        body: formData
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Failed to process report document.');
      }

      setReportData(data);
      Alert.alert('Report Processed!', `Analyzed ${data.metrics?.length || 0} biomarkers successfully.`);
    } catch (err) {
      console.error('Upload Error:', err);
      setErrorMessage(err.message || 'Unable to connect to AXON backend service.');
    } finally {
      setUploading(false);
    }
  };

  // Download PDF Report
  const handleDownloadPdf = async () => {
    if (!reportData) return;
    try {
      const response = await fetch(`${API_HOST}/api/v1/reports/export-pdf`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: 'Scanned_Report.pdf',
          status: 'success',
          metrics: reportData.metrics || [],
          disease_risks: reportData.disease_risks || [],
          has_critical_alert: reportData.has_critical_alert || false,
          critical_alerts: reportData.critical_alerts || [],
          patient_summary: reportData.patient_summary || '',
          language: selectedLanguage
        })
      });

      if (response.ok) {
        Alert.alert('PDF Summary Ready! 📥', '1-Page Patient Health Summary PDF generated successfully.');
      } else {
        Alert.alert('PDF Error', 'Failed to generate PDF document.');
      }
    } catch (err) {
      Alert.alert('Network Error', 'Verify backend connection to download PDF.');
    }
  };

  // Send Chat Message
  const handleSendChatMessage = async (customPrompt) => {
    const queryToSend = customPrompt || currentQuery;
    if (!queryToSend.trim()) return;

    const userMessage = queryToSend;
    const updatedHistory = [...chatMessages, { role: 'user', content: userMessage }];
    setChatMessages(updatedHistory);
    if (!customPrompt) setCurrentQuery('');
    setChatLoading(true);

    try {
      const response = await fetch(`${API_HOST}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          current_message: userMessage,
          extracted_metrics: reportData?.metrics || [],
          selected_tone: selectedTone,
          language: selectedLanguage,
          chat_history: updatedHistory.map(m => ({
            role: m.role === 'user' ? 'user' : 'model',
            content: m.content
          }))
        })
      });

      const data = await response.json();
      if (response.ok) {
        setChatMessages(prev => [...prev, { role: 'model', content: data.response }]);
        setChatDisclaimer(data.disclaimer);
      } else {
        setChatMessages(prev => [...prev, { role: 'model', content: 'Unable to process question. Please try again.' }]);
      }
    } catch (err) {
      setChatMessages(prev => [...prev, { role: 'model', content: 'Network error. Verify backend server connection.' }]);
    } finally {
      setChatLoading(false);
    }
  };

  // Helper for biomarker gauge calculation
  const getGaugePercentage = (val, min, max) => {
    if (min >= max || isNaN(val)) return 50;
    if (val <= min) return 15;
    if (val >= max) return 85;
    return Math.min(Math.max(15 + ((val - min) / (max - min)) * 70, 10), 90);
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#090d16" />
      
      {/* App Header */}
      <View style={styles.header}>
        <View style={styles.brandContainer}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoText}>A</Text>
          </View>
          <View>
            <Text style={styles.headerTitle}>AXON Mobile</Text>
            <Text style={styles.headerSubtitle}>AI Clinical Intelligence Console</Text>
          </View>
        </View>

        <View style={styles.headerRightBadge}>
          <View style={styles.onlineDot} />
          <Text style={styles.onlineText}>AI Ready</Text>
        </View>
      </View>

      {/* Main Body */}
      {activeTab === 'dashboard' ? (
        <ScrollView contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>
          
          {/* File Picker & Camera Card */}
          <View style={styles.card}>
            <View style={styles.uploadHeaderRow}>
              <View style={styles.uploadIconBadge}>
                <Text style={styles.uploadIconText}>✦</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={styles.cardTitle}>Scan Lab Report</Text>
                <Text style={styles.cardSubtitle}>Blood, Metabolic, Urine or Thyroid panels</Text>
              </View>
            </View>
            
            {/* Language Selector */}
            <View style={styles.languageContainer}>
              <Text style={styles.label}>TRANSLATION LANGUAGE</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 4 }}>
                {['English', 'Tamil', 'Hindi', 'Telugu'].map((lang) => (
                  <TouchableOpacity
                    key={lang}
                    style={[styles.langBadge, selectedLanguage === lang && styles.langBadgeActive]}
                    onPress={() => setSelectedLanguage(lang)}
                    activeOpacity={0.7}
                  >
                    <Text style={[styles.langBadgeText, selectedLanguage === lang && styles.langBadgeTextActive]}>{lang}</Text>
                  </TouchableOpacity>
                ))}
              </ScrollView>
            </View>

            <View style={styles.buttonRow}>
              <TouchableOpacity style={styles.btnSecondary} onPress={handleTakePhoto} activeOpacity={0.8}>
                <Text style={styles.btnSecondaryText}>📷 Camera Scan</Text>
              </TouchableOpacity>
              <TouchableOpacity style={styles.btnPrimary} onPress={handlePickDocument} activeOpacity={0.8}>
                <Text style={styles.btnPrimaryText}>📁 Browse PDF</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Loader */}
          {uploading && (
            <View style={[styles.card, styles.centerCard]}>
              <ActivityIndicator size="large" color="#06b6d4" />
              <Text style={styles.loadingText}>Analyzing Biomarkers with AI Parser...</Text>
              <Text style={styles.loadingSub}>Extracting values, scrubbing PII & mapping ranges</Text>
            </View>
          )}

          {/* Error Banner */}
          {errorMessage && !uploading && (
            <View style={[styles.card, styles.errorCard]}>
              <Text style={styles.errorText}>❌ {errorMessage}</Text>
            </View>
          )}

          {/* Analysis Results Display */}
          {reportData && !uploading && (
            <View style={{ gap: 16 }}>
              
              {/* Emergency Critical Panic Red Flag Alert */}
              {(reportData.has_critical_alert || (reportData.critical_alerts && reportData.critical_alerts.length > 0)) && (
                <View style={styles.criticalCard}>
                  <Text style={styles.criticalTitle}>
                    🚨 EMERGENCY CRITICAL ALERT
                  </Text>
                  <Text style={styles.criticalSub}>
                    One or more test parameters have hit hard emergency panic limits. Please seek immediate emergency medical care.
                  </Text>
                  {reportData.critical_alerts?.map((alertStr, i) => (
                    <View key={i} style={styles.criticalItem}>
                      <Text style={styles.criticalItemText}>• {alertStr}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Patient Summary Card */}
              {reportData.patient_summary && (
                <View style={styles.summaryCard}>
                  <View style={styles.summaryHeader}>
                    <Text style={styles.summaryTitle}>✦ Empathetic Summary ({selectedLanguage})</Text>
                    <TouchableOpacity style={styles.exportBtn} onPress={handleDownloadPdf} activeOpacity={0.7}>
                      <Text style={styles.exportBtnText}>📥 Export PDF</Text>
                    </TouchableOpacity>
                  </View>
                  <Text style={styles.summaryText}>{reportData.patient_summary}</Text>
                </View>
              )}

              {/* Disease Risk Patterns Card */}
              {reportData.disease_risks && reportData.disease_risks.length > 0 && (
                <View style={styles.card}>
                  <Text style={styles.cardTitle}>⚠️ Multi-Biomarker Disease Risks</Text>
                  <Text style={styles.cardSubtitle}>Predicted patterns based on physiological interactions</Text>
                  {reportData.disease_risks.map((risk, i) => (
                    <View key={i} style={styles.riskBadge}>
                      <Text style={styles.riskBadgeText}>• {risk}</Text>
                    </View>
                  ))}
                </View>
              )}

              {/* Biomarkers Parameter List */}
              <View style={styles.card}>
                <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <Text style={styles.cardTitle}>Extracted Lab Biomarkers</Text>
                  <View style={styles.countBadge}>
                    <Text style={styles.countBadgeText}>{reportData.metrics?.length || 0} Total</Text>
                  </View>
                </View>

                {reportData.metrics?.map((metric, idx) => {
                  const status = metric.status.toLowerCase();
                  let badgeStyle = styles.statusNormal;
                  let fillStyle = styles.gaugeFillNormal;
                  let pulseColor = '#10b981';

                  if (status === 'low') {
                    badgeStyle = styles.statusLow;
                    fillStyle = styles.gaugeFillLow;
                    pulseColor = '#f59e0b';
                  } else if (status === 'high') {
                    badgeStyle = styles.statusHigh;
                    fillStyle = styles.gaugeFillHigh;
                    pulseColor = '#ef4444';
                  }

                  const isLowConf = metric.is_low_confidence || (metric.confidence !== undefined && metric.confidence < 0.80);
                  const confPct = metric.confidence ? Math.round(metric.confidence * 100) : 95;
                  const pct = getGaugePercentage(metric.value, metric.min_normal, metric.max_normal);

                  return (
                    <View key={idx} style={styles.metricCardItem}>
                      <View style={styles.metricHeaderRow}>
                        <Text style={styles.metricName}>{metric.biomarker_name}</Text>
                        <View style={[styles.statusBadge, badgeStyle]}>
                          <View style={[styles.pulseDot, { backgroundColor: pulseColor }]} />
                          <Text style={styles.statusBadgeText}>{metric.status}</Text>
                        </View>
                      </View>

                      <View style={styles.metricValueRow}>
                        <Text style={styles.metricValue}>{metric.value}</Text>
                        <Text style={styles.metricUnit}>{metric.unit}</Text>
                      </View>

                      {/* Range Gauge Slider */}
                      <View style={styles.gaugeTrack}>
                        <View style={[styles.gaugeFill, fillStyle, { width: `${pct}%` }]} />
                      </View>

                      <View style={styles.metricFooterRow}>
                        <Text style={styles.metricRange}>Target: {metric.min_normal} - {metric.max_normal}</Text>
                        <Text style={[styles.confText, isLowConf && styles.confLowText]}>
                          {isLowConf ? `⚠️ ${confPct}% Conf` : `✓ ${confPct}% Conf`}
                        </Text>
                      </View>

                      {isLowConf && (
                        <View style={styles.lowConfBanner}>
                          <Text style={styles.lowConfText}>
                            ⚠️ Low Confidence ({confPct}%) — Verify against paper report.
                          </Text>
                        </View>
                      )}
                    </View>
                  );
                })}
              </View>

            </View>
          )}

          {/* Bottom spacing for floating tab bar */}
          <View style={{ height: 75 }} />

        </ScrollView>
      ) : (
        
        /* Chatbot View */
        <View style={styles.chatContainer}>
          
          {/* AI Assistant Avatar Header */}
          <View style={styles.aiHeaderCard}>
            <View style={styles.aiAvatar}>
              <Text style={styles.aiAvatarText}>🤖</Text>
            </View>
            <View style={{ flex: 1 }}>
              <Text style={styles.aiTitle}>AXON Medical Companion</Text>
              <Text style={styles.aiSub}>Context-aware clinical triage & report insights</Text>
            </View>
          </View>

          {/* Tone Selector */}
          <View style={styles.toneContainer}>
            <Text style={styles.label}>COMPANION TONE</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginTop: 4 }}>
              {['Empathetic', 'Clinical', 'Educational', 'Family'].map((tone) => (
                <TouchableOpacity
                  key={tone}
                  style={[styles.toneBadge, selectedTone === tone && styles.toneBadgeActive]}
                  onPress={() => setSelectedTone(tone)}
                  activeOpacity={0.7}
                >
                  <Text style={[styles.toneBadgeText, selectedTone === tone && styles.toneBadgeTextActive]}>{tone}</Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Messages Scroll Area */}
          <ScrollView style={styles.chatScroll} contentContainerStyle={{ gap: 12, paddingBottom: 16 }} showsVerticalScrollIndicator={false}>
            {chatMessages.length === 0 ? (
              <View style={styles.emptyChatContainer}>
                <View style={styles.chatWelcomeIcon}>
                  <Text style={{ fontSize: 32 }}>💬</Text>
                </View>
                <Text style={styles.emptyChatTitle}>How can AXON help you?</Text>
                <Text style={styles.emptyChatSub}>
                  Ask questions about your uploaded blood metrics, normal ranges, or dietary advice.
                </Text>

                {/* Quick Suggestion Pills */}
                <View style={styles.suggestionRow}>
                  <TouchableOpacity style={styles.suggestionPill} onPress={() => handleSendChatMessage("Can you explain my overall report summary?")}>
                    <Text style={styles.suggestionText}>✨ Summarize my report</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.suggestionPill} onPress={() => handleSendChatMessage("Are there any dietary changes I should make?")}>
                    <Text style={styles.suggestionText}>🥗 Dietary recommendations</Text>
                  </TouchableOpacity>
                  <TouchableOpacity style={styles.suggestionPill} onPress={() => handleSendChatMessage("What follow-up tests are usually needed?")}>
                    <Text style={styles.suggestionText}>🩺 Recommended tests</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ) : (
              chatMessages.map((msg, idx) => (
                <View
                  key={idx}
                  style={[
                    styles.chatBubble,
                    msg.role === 'user' ? styles.userBubble : styles.modelBubble
                  ]}
                >
                  <Text style={[styles.chatBubbleText, msg.role === 'user' ? styles.userBubbleText : styles.modelBubbleText]}>
                    {msg.content}
                  </Text>
                </View>
              ))
            )}
            {chatLoading && (
              <View style={styles.loadingBubble}>
                <ActivityIndicator size="small" color="#06b6d4" />
                <Text style={styles.loadingBubbleText}>AXON is reviewing clinical parameters...</Text>
              </View>
            )}
          </ScrollView>

          {chatDisclaimer ? <Text style={styles.disclaimerText}>{chatDisclaimer}</Text> : null}

          {/* Chat Input */}
          <View style={styles.chatInputRow}>
            <TextInput
              style={styles.chatInput}
              placeholder="Ask AXON a clinical question..."
              placeholderTextColor="#64748b"
              value={currentQuery}
              onChangeText={setCurrentQuery}
            />
            <TouchableOpacity style={styles.sendButton} onPress={() => handleSendChatMessage()} activeOpacity={0.8}>
              <Text style={styles.sendButtonText}>Send</Text>
            </TouchableOpacity>
          </View>

          {/* Bottom spacing for floating tab bar */}
          <View style={{ height: 60 }} />

        </View>
      )}

      {/* Floating Bottom Navigation Dock */}
      <View style={styles.bottomDockWrapper}>
        <View style={styles.bottomDock}>
          <TouchableOpacity
            style={[styles.dockItem, activeTab === 'dashboard' && styles.dockItemActive]}
            onPress={() => setActiveTab('dashboard')}
            activeOpacity={0.8}
          >
            <Text style={[styles.dockItemText, activeTab === 'dashboard' && styles.dockItemTextActive]}>📊 Report</Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.dockItem, activeTab === 'chat' && styles.dockItemActive]}
            onPress={() => setActiveTab('chat')}
            activeOpacity={0.8}
          >
            <Text style={[styles.dockItemText, activeTab === 'chat' && styles.dockItemTextActive]}>💬 AI Chat</Text>
          </TouchableOpacity>
        </View>
      </View>

    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#090d16'
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 14,
    backgroundColor: '#111726',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255, 255, 255, 0.08)',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  brandContainer: {
    flexDirection: 'row',
    alignItems: 'center'
  },
  logoBadge: {
    width: 42,
    height: 42,
    borderRadius: 14,
    backgroundColor: '#06b6d4',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    shadowColor: '#06b6d4',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 6
  },
  logoText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 22
  },
  headerTitle: {
    color: '#f8fafc',
    fontSize: 18,
    fontWeight: '800'
  },
  headerSubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '500'
  },
  headerRightBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(16, 185, 129, 0.12)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.25)',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 20,
    gap: 6
  },
  onlineDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#10b981'
  },
  onlineText: {
    color: '#34d399',
    fontSize: 11,
    fontWeight: '700'
  },
  scrollContent: {
    padding: 16,
    gap: 16
  },
  card: {
    backgroundColor: '#111726',
    borderRadius: 22,
    padding: 18,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 4
  },
  uploadHeaderRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 16
  },
  uploadIconBadge: {
    width: 44,
    height: 44,
    borderRadius: 14,
    backgroundColor: 'rgba(6, 182, 212, 0.14)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.3)'
  },
  uploadIconText: {
    fontSize: 20,
    color: '#06b6d4',
    fontWeight: 'bold'
  },
  centerCard: {
    alignItems: 'center',
    paddingVertical: 28
  },
  cardTitle: {
    color: '#f8fafc',
    fontSize: 16,
    fontWeight: '800'
  },
  cardSubtitle: {
    color: '#94a3b8',
    fontSize: 12,
    marginTop: 2
  },
  label: {
    color: '#64748b',
    fontSize: 11,
    fontWeight: '700',
    letterSpacing: 0.5,
    marginBottom: 6
  },
  languageContainer: {
    marginBottom: 16
  },
  langBadge: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: '#182033',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginRight: 8
  },
  langBadgeActive: {
    backgroundColor: 'rgba(6, 182, 212, 0.15)',
    borderColor: '#06b6d4'
  },
  langBadgeText: {
    color: '#94a3b8',
    fontSize: 12,
    fontWeight: '600'
  },
  langBadgeTextActive: {
    color: '#06b6d4',
    fontWeight: '700'
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12
  },
  btnPrimary: {
    flex: 1,
    backgroundColor: '#06b6d4',
    paddingVertical: 13,
    borderRadius: 25,
    alignItems: 'center',
    shadowColor: '#06b6d4',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.35,
    shadowRadius: 8,
    elevation: 4
  },
  btnPrimaryText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 14
  },
  btnSecondary: {
    flex: 1,
    backgroundColor: '#182033',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    paddingVertical: 13,
    borderRadius: 25,
    alignItems: 'center'
  },
  btnSecondaryText: {
    color: '#f8fafc',
    fontWeight: '700',
    fontSize: 14
  },
  loadingText: {
    color: '#06b6d4',
    marginTop: 14,
    fontWeight: '700',
    fontSize: 15
  },
  loadingSub: {
    color: '#64748b',
    fontSize: 12,
    marginTop: 4
  },
  errorCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    borderColor: 'rgba(239, 68, 68, 0.3)'
  },
  errorText: {
    color: '#f87171',
    fontSize: 13,
    fontWeight: '600'
  },
  criticalCard: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderColor: '#ef4444',
    borderWidth: 2,
    borderRadius: 20,
    padding: 16
  },
  criticalTitle: {
    color: '#f87171',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4
  },
  criticalSub: {
    color: '#f8fafc',
    fontSize: 13,
    lineHeight: 18,
    marginBottom: 10,
    fontWeight: '600'
  },
  criticalItem: {
    backgroundColor: 'rgba(239, 68, 68, 0.25)',
    padding: 8,
    borderRadius: 8,
    marginTop: 4
  },
  criticalItemText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700'
  },
  summaryCard: {
    backgroundColor: 'rgba(6, 182, 212, 0.08)',
    borderLeftWidth: 4,
    borderLeftColor: '#06b6d4',
    padding: 16,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.2)'
  },
  summaryHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  summaryTitle: {
    color: '#06b6d4',
    fontWeight: '800',
    fontSize: 14
  },
  exportBtn: {
    backgroundColor: '#06b6d4',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 14
  },
  exportBtnText: {
    color: '#ffffff',
    fontSize: 11,
    fontWeight: '800'
  },
  summaryText: {
    color: '#f8fafc',
    fontSize: 13,
    lineHeight: 20
  },
  riskBadge: {
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.25)',
    padding: 12,
    borderRadius: 12,
    marginTop: 8
  },
  riskBadgeText: {
    color: '#f87171',
    fontWeight: '600',
    fontSize: 13
  },
  countBadge: {
    backgroundColor: 'rgba(6, 182, 212, 0.12)',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.25)'
  },
  countBadgeText: {
    color: '#06b6d4',
    fontSize: 11,
    fontWeight: '700'
  },
  metricCardItem: {
    backgroundColor: '#182033',
    padding: 14,
    borderRadius: 16,
    marginTop: 10,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.05)'
  },
  metricHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  metricName: {
    color: '#f8fafc',
    fontWeight: '800',
    fontSize: 14
  },
  statusBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 5,
    paddingHorizontal: 9,
    paddingVertical: 4,
    borderRadius: 14
  },
  pulseDot: {
    width: 6,
    height: 6,
    borderRadius: 3
  },
  statusBadgeText: {
    fontSize: 10,
    fontWeight: '800',
    textTransform: 'uppercase'
  },
  statusNormal: {
    backgroundColor: 'rgba(16, 185, 129, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(16, 185, 129, 0.3)'
  },
  statusLow: {
    backgroundColor: 'rgba(245, 158, 11, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(245, 158, 11, 0.3)'
  },
  statusHigh: {
    backgroundColor: 'rgba(239, 68, 68, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.3)'
  },
  metricValueRow: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginTop: 6
  },
  metricValue: {
    color: '#f8fafc',
    fontSize: 22,
    fontWeight: '800'
  },
  metricUnit: {
    color: '#94a3b8',
    fontSize: 12,
    marginLeft: 4,
    fontWeight: '600'
  },
  gaugeTrack: {
    height: 5,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 3,
    marginVertical: 8,
    overflow: 'hidden'
  },
  gaugeFill: {
    height: '100%',
    borderRadius: 3
  },
  gaugeFillNormal: { backgroundColor: '#10b981' },
  gaugeFillLow: { backgroundColor: '#f59e0b' },
  gaugeFillHigh: { backgroundColor: '#ef4444' },
  metricFooterRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  metricRange: {
    color: '#64748b',
    fontSize: 11
  },
  confText: {
    fontSize: 10,
    color: '#64748b',
    fontWeight: '600'
  },
  confLowText: {
    color: '#f87171',
    fontWeight: '800'
  },
  lowConfBanner: {
    backgroundColor: 'rgba(239, 68, 68, 0.12)',
    padding: 8,
    borderRadius: 8,
    marginTop: 8
  },
  lowConfText: {
    color: '#f87171',
    fontSize: 11,
    fontWeight: '700'
  },

  // Chatbot Styles
  chatContainer: {
    flex: 1,
    paddingHorizontal: 16,
    paddingTop: 12
  },
  aiHeaderCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#111726',
    borderRadius: 18,
    padding: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    marginBottom: 12,
    gap: 12
  },
  aiAvatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(6, 182, 212, 0.15)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.3)'
  },
  aiAvatarText: {
    fontSize: 20
  },
  aiTitle: {
    color: '#f8fafc',
    fontSize: 14,
    fontWeight: '800'
  },
  aiSub: {
    color: '#94a3b8',
    fontSize: 11
  },
  toneContainer: {
    marginBottom: 10
  },
  toneBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#182033',
    marginRight: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)'
  },
  toneBadgeActive: {
    backgroundColor: 'rgba(6, 182, 212, 0.15)',
    borderColor: '#06b6d4'
  },
  toneBadgeText: {
    color: '#94a3b8',
    fontSize: 11,
    fontWeight: '600'
  },
  toneBadgeTextActive: {
    color: '#06b6d4',
    fontWeight: '800'
  },
  chatScroll: {
    flex: 1,
    backgroundColor: '#111726',
    borderRadius: 20,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)'
  },
  emptyChatContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 24
  },
  chatWelcomeIcon: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: 'rgba(6, 182, 212, 0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 12
  },
  emptyChatTitle: {
    color: '#f8fafc',
    fontSize: 16,
    fontWeight: '800',
    marginBottom: 4
  },
  emptyChatSub: {
    color: '#94a3b8',
    fontSize: 12,
    textAlign: 'center',
    paddingHorizontal: 16,
    lineHeight: 18
  },
  suggestionRow: {
    marginTop: 18,
    gap: 8,
    width: '100%'
  },
  suggestionPill: {
    backgroundColor: '#182033',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.2)',
    alignItems: 'center'
  },
  suggestionText: {
    color: '#06b6d4',
    fontSize: 12,
    fontWeight: '700'
  },
  chatBubble: {
    maxWidth: '82%',
    padding: 12,
    borderRadius: 16
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#06b6d4',
    borderBottomRightRadius: 3
  },
  userBubbleText: {
    color: '#ffffff',
    fontWeight: '600'
  },
  modelBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#182033',
    borderColor: 'rgba(255, 255, 255, 0.08)',
    borderWidth: 1,
    borderBottomLeftRadius: 3
  },
  modelBubbleText: {
    color: '#f8fafc'
  },
  chatBubbleText: {
    fontSize: 13,
    lineHeight: 19
  },
  loadingBubble: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    alignSelf: 'flex-start',
    backgroundColor: '#182033',
    padding: 10,
    borderRadius: 14
  },
  loadingBubbleText: {
    color: '#94a3b8',
    fontSize: 11,
    fontStyle: 'italic'
  },
  disclaimerText: {
    color: '#64748b',
    fontSize: 10,
    fontStyle: 'italic',
    textAlign: 'center',
    marginVertical: 4
  },
  chatInputRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8
  },
  chatInput: {
    flex: 1,
    backgroundColor: '#111726',
    borderRadius: 25,
    paddingHorizontal: 16,
    paddingVertical: 10,
    color: '#f8fafc',
    fontSize: 13,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)'
  },
  sendButton: {
    backgroundColor: '#06b6d4',
    paddingHorizontal: 18,
    borderRadius: 25,
    justifyContent: 'center',
    shadowColor: '#06b6d4',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 3
  },
  sendButtonText: {
    color: '#ffffff',
    fontWeight: '800',
    fontSize: 13
  },

  // Floating Bottom Dock
  bottomDockWrapper: {
    position: 'absolute',
    bottom: 16,
    left: 24,
    right: 24,
    alignItems: 'center'
  },
  bottomDock: {
    flexDirection: 'row',
    backgroundColor: '#111726',
    borderRadius: 30,
    padding: 4,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.12)',
    shadowColor: '#000000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.45,
    shadowRadius: 16,
    elevation: 8,
    width: '100%',
    maxWidth: 320
  },
  dockItem: {
    flex: 1,
    paddingVertical: 10,
    alignItems: 'center',
    borderRadius: 25
  },
  dockItemActive: {
    backgroundColor: '#06b6d4',
    shadowColor: '#06b6d4',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.35,
    shadowRadius: 6,
    elevation: 3
  },
  dockItemText: {
    color: '#94a3b8',
    fontWeight: '700',
    fontSize: 13
  },
  dockItemTextActive: {
    color: '#ffffff'
  }
});
