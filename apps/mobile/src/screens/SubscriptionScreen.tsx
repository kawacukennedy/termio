import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  SafeAreaView,
  Alert,
  Modal,
} from 'react-native';
import Icon from 'react-native-vector-icons/Ionicons';
import { useAppStore } from '../store/appStore';

interface Plan {
  id: string;
  name: string;
  tier: string;
  price_monthly: number;
  price_yearly: number;
  features: string[];
  device_limit: number;
}

export default function SubscriptionScreen({ navigation }: any) {
  const serverUrl = useAppStore((state) => state.serverUrl);
  const [currentPlan, setCurrentPlan] = useState<string>('freemium');
  const [plans, setPlans] = useState<Plan[]>([]);
  const [showPlans, setShowPlans] = useState(false);

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await fetch(`${serverUrl}/api/subscriptions/plans`);
      if (response.ok) {
        const data = await response.json();
        setPlans(data);
      }
    } catch (error) {
      console.log('Error fetching plans:', error);
    }
  };

  const getCurrentPlanDetails = () => {
    return plans.find(p => p.tier === currentPlan) || plans[0];
  };

  const handleSubscribe = (plan: Plan) => {
    Alert.alert(
      `Subscribe to ${plan.name}`,
      `Would you like to upgrade to ${plan.name} for $${plan.price_monthly}/month?`,
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Subscribe', 
          onPress: () => {
            setCurrentPlan(plan.tier);
            setShowPlans(false);
            Alert.alert('Success', `You are now subscribed to ${plan.name}!`);
          }
        },
      ]
    );
  };

  const current = getCurrentPlanDetails();

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Icon name="chevron-back" size={24} color="#FAFAFA" />
        </TouchableOpacity>
        <Text style={styles.headerTitle}>Subscription</Text>
        <View style={{ width: 24 }} />
      </View>

      <ScrollView style={styles.content}>
        {/* Current Plan */}
        <View style={styles.currentPlanCard}>
          <View style={styles.planHeader}>
            <Text style={styles.planLabel}>Current Plan</Text>
            <View style={[styles.planBadge, currentPlan === 'freemium' && styles.badgeFree]}>
              <Text style={styles.planBadgeText}>{current?.name || 'Freemium'}</Text>
            </View>
          </View>
          
          <Text style={styles.planPrice}>
            {current?.price_monthly === 0 ? 'Free' : `$${current?.price_monthly}/month`}
          </Text>
          
          <View style={styles.planFeatures}>
            <Text style={styles.featuresTitle}>Your features:</Text>
            {current?.features.slice(0, 4).map((feature, index) => (
              <View key={index} style={styles.featureItem}>
                <Icon name="checkmark-circle" size={16} color="#10B981" />
                <Text style={styles.featureText}>{feature}</Text>
              </View>
            ))}
          </View>

          <TouchableOpacity 
            style={styles.manageButton}
            onPress={() => setShowPlans(true)}
          >
            <Text style={styles.manageButtonText}>
              {currentPlan === 'freemium' ? 'Upgrade Plan' : 'Change Plan'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Subscription Details */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account Details</Text>
          
          <View style={styles.detailItem}>
            <Icon name="person-outline" size={20} color="#A3A3A3" />
            <View style={styles.detailInfo}>
              <Text style={styles.detailLabel}>Account Type</Text>
              <Text style={styles.detailValue}>{current?.name || 'Freemium'}</Text>
            </View>
          </View>

          <View style={styles.detailItem}>
            <Icon name="devices-outline" size={20} color="#A3A3A3" />
            <View style={styles.detailInfo}>
              <Text style={styles.detailLabel}>Devices</Text>
              <Text style={styles.detailValue}>
                {current?.device_limit === -1 ? 'Unlimited' : `${current?.device_limit || 1} device(s)`}
              </Text>
            </View>
          </View>

          <View style={styles.detailItem}>
            <Icon name="cloud-outline" size={20} color="#A3A3A3" />
            <View style={styles.detailInfo}>
              <Text style={styles.detailLabel}>Model Storage</Text>
              <Text style={styles.detailValue}>
                {current?.device_limit === -1 ? 'Unlimited' : `Up to ${current?.device_limit || 2}GB`}
              </Text>
            </View>
          </View>
        </View>

        {/* Billing History */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Billing</Text>
          
          <TouchableOpacity style={styles.billingItem}>
            <Icon name="receipt-outline" size={20} color="#A3A3A3" />
            <View style={styles.detailInfo}>
              <Text style={styles.detailLabel}>Billing History</Text>
              <Text style={styles.detailValue}>View past invoices</Text>
            </View>
            <Icon name="chevron-forward" size={20} color="#525252" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.billingItem}>
            <Icon name="card-outline" size={20} color="#A3A3A3" />
            <View style={styles.detailInfo}>
              <Text style={styles.detailLabel}>Payment Methods</Text>
              <Text style={styles.detailValue}>Add or manage cards</Text>
            </View>
            <Icon name="chevron-forward" size={20} color="#525252" />
          </TouchableOpacity>
        </View>
      </ScrollView>

      {/* Plans Modal */}
      <Modal
        visible={showPlans}
        animationType="slide"
        transparent={true}
        onRequestClose={() => setShowPlans(false)}
      >
        <View style={styles.modalOverlay}>
          <View style={styles.modalContent}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>Choose a Plan</Text>
              <TouchableOpacity onPress={() => setShowPlans(false)}>
                <Icon name="close" size={24} color="#FAFAFA" />
              </TouchableOpacity>
            </View>

            <ScrollView style={styles.plansList}>
              {plans.map((plan) => (
                <TouchableOpacity 
                  key={plan.id}
                  style={[
                    styles.planOption,
                    currentPlan === plan.tier && styles.planOptionActive
                  ]}
                  onPress={() => handleSubscribe(plan)}
                >
                  <View style={styles.planOptionHeader}>
                    <Text style={styles.planOptionName}>{plan.name}</Text>
                    {plan.tier === 'pro' && (
                      <View style={styles.popularBadge}>
                        <Text style={styles.popularBadgeText}>Popular</Text>
                      </View>
                    )}
                  </View>
                  <Text style={styles.planOptionPrice}>
                    {plan.price_monthly === 0 ? 'Free' : `$${plan.price_monthly}/mo`}
                  </Text>
                  <View style={styles.planOptionFeatures}>
                    {plan.features.slice(0, 3).map((feature, index) => (
                      <View key={index} style={styles.featureItem}>
                        <Icon name="checkmark" size={14} color="#10B981" />
                        <Text style={styles.featureTextSmall}>{feature}</Text>
                      </View>
                    ))}
                  </View>
                  {currentPlan === plan.tier && (
                    <View style={styles.currentBadge}>
                      <Text style={styles.currentBadgeText}>Current Plan</Text>
                    </View>
                  )}
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        </View>
      </Modal>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0C0C0C',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  content: {
    flex: 1,
  },
  currentPlanCard: {
    margin: 16,
    padding: 20,
    backgroundColor: '#171717',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#0EA5E9',
  },
  planHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  planLabel: {
    fontSize: 14,
    color: '#A3A3A3',
  },
  planBadge: {
    backgroundColor: '#0EA5E9',
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  badgeFree: {
    backgroundColor: '#404040',
  },
  planBadgeText: {
    color: '#FFFFFF',
    fontSize: 12,
    fontWeight: '600',
  },
  planPrice: {
    fontSize: 36,
    fontWeight: '700',
    color: '#FAFAFA',
    marginBottom: 16,
  },
  planFeatures: {
    marginBottom: 16,
  },
  featuresTitle: {
    fontSize: 14,
    color: '#A3A3A3',
    marginBottom: 8,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 6,
  },
  featureText: {
    fontSize: 14,
    color: '#FAFAFA',
    flex: 1,
  },
  featureTextSmall: {
    fontSize: 12,
    color: '#A3A3A3',
    flex: 1,
  },
  manageButton: {
    backgroundColor: '#0EA5E9',
    padding: 14,
    borderRadius: 10,
    alignItems: 'center',
  },
  manageButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
  },
  section: {
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  sectionTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#737373',
    marginBottom: 12,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 12,
  },
  billingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    gap: 12,
  },
  detailInfo: {
    flex: 1,
  },
  detailLabel: {
    fontSize: 16,
    color: '#FAFAFA',
  },
  detailValue: {
    fontSize: 14,
    color: '#737373',
    marginTop: 2,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.9)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#171717',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    maxHeight: '80%',
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#262626',
  },
  modalTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  plansList: {
    padding: 16,
  },
  planOption: {
    backgroundColor: '#262626',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  planOptionActive: {
    borderColor: '#0EA5E9',
  },
  planOptionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  planOptionName: {
    fontSize: 18,
    fontWeight: '600',
    color: '#FAFAFA',
  },
  popularBadge: {
    backgroundColor: '#F59E0B',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  popularBadgeText: {
    color: '#000000',
    fontSize: 10,
    fontWeight: '700',
  },
  planOptionPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#FAFAFA',
    marginBottom: 12,
  },
  planOptionFeatures: {
    gap: 4,
  },
  currentBadge: {
    marginTop: 12,
    backgroundColor: '#0EA5E920',
    padding: 8,
    borderRadius: 8,
    alignItems: 'center',
  },
  currentBadgeText: {
    color: '#0EA5E9',
    fontSize: 12,
    fontWeight: '600',
  },
});
