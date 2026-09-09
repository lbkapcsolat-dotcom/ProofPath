import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from 'react-native';
import { analyzeEvidence } from './src/evidence.mjs';
import { getRevenueCatService } from './src/revenuecat-native';

const verdictTone = {
  SUPPORTED: '#176B45',
  CONTRADICTED: '#9B2C2C',
  INSUFFICIENT: '#7A5A00',
};

function Card({ children }) {
  return (
    <View style={{ gap: 10, padding: 16, borderRadius: 18, borderWidth: 1, borderColor: '#D8DDE6', backgroundColor: '#FFFFFF' }}>
      {children}
    </View>
  );
}

export default function App() {
  const [claim, setClaim] = useState('Solar panels reduced school electricity use');
  const [evidence, setEvidence] = useState('School electricity use was reduced after solar panels were installed');
  const [analysis, setAnalysis] = useState(() => analyzeEvidence(claim, evidence));
  const [rcState, setRcState] = useState({ state: 'LOADING', isPremium: false, packageToBuy: null });
  const [purchaseBusy, setPurchaseBusy] = useState(false);
  const [purchaseMessage, setPurchaseMessage] = useState('');

  const service = useMemo(() => getRevenueCatService(), []);

  useEffect(() => {
    let active = true;
    service.bootstrap()
      .then((next) => { if (active) setRcState(next); })
      .catch((error) => { if (active) setRcState({ state: 'ERROR', isPremium: false, packageToBuy: null, error: String(error?.message ?? error) }); });
    return () => { active = false; };
  }, [service]);

  async function handlePurchase() {
    setPurchaseBusy(true);
    setPurchaseMessage('');
    try {
      const result = await service.purchase(rcState.packageToBuy);
      setRcState((current) => ({ ...current, state: result.state, isPremium: result.isPremium }));
      setPurchaseMessage(result.isPremium ? 'Evidence Plus unlocked in RevenueCat Test Store.' : `Purchase state: ${result.state}`);
    } catch (error) {
      if (error?.userCancelled) setPurchaseMessage('Test purchase cancelled.');
      else setPurchaseMessage(`Test purchase failed: ${String(error?.message ?? error)}`);
    } finally {
      setPurchaseBusy(false);
    }
  }

  return (
    <ScrollView contentInsetAdjustmentBehavior="automatic" contentContainerStyle={{ padding: 20, gap: 16, backgroundColor: '#F4F6F9', minHeight: '100%' }}>
      <View style={{ gap: 6, paddingTop: 18 }}>
        <Text selectable style={{ fontSize: 30, fontWeight: '800', color: '#18202A' }}>Evidence Coach Pocket</Text>
        <Text selectable style={{ fontSize: 16, lineHeight: 22, color: '#4A5565' }}>A bounded evidence-reasoning coach with a RevenueCat Test Store unlock path.</Text>
      </View>

      <Card>
        <Text selectable style={{ fontSize: 18, fontWeight: '700' }}>1. Claim</Text>
        <TextInput
          value={claim}
          onChangeText={setClaim}
          multiline
          placeholder="Enter a claim"
          style={{ minHeight: 78, borderWidth: 1, borderColor: '#CBD2DC', borderRadius: 14, padding: 12, backgroundColor: '#FAFBFC', textAlignVertical: 'top' }}
        />
        <Text selectable style={{ fontSize: 18, fontWeight: '700' }}>2. Evidence</Text>
        <TextInput
          value={evidence}
          onChangeText={setEvidence}
          multiline
          placeholder="Enter a source-backed observation"
          style={{ minHeight: 96, borderWidth: 1, borderColor: '#CBD2DC', borderRadius: 14, padding: 12, backgroundColor: '#FAFBFC', textAlignVertical: 'top' }}
        />
        <Pressable
          onPress={() => setAnalysis(analyzeEvidence(claim, evidence))}
          style={({ pressed }) => ({ padding: 14, borderRadius: 14, backgroundColor: pressed ? '#264D9B' : '#315FC0', alignItems: 'center' })}
        >
          <Text selectable style={{ color: '#FFFFFF', fontWeight: '800', fontSize: 16 }}>Analyze evidence</Text>
        </Pressable>
      </Card>

      <Card>
        <Text selectable style={{ fontSize: 13, fontWeight: '800', letterSpacing: 1, color: verdictTone[analysis.verdict] }}>{analysis.verdict}</Text>
        <Text selectable style={{ fontSize: 17, lineHeight: 24, color: '#202833' }}>{analysis.reason}</Text>
        <View style={{ padding: 12, borderRadius: 12, backgroundColor: '#EEF2F8' }}>
          <Text selectable style={{ fontWeight: '700', color: '#293446' }}>Next evidence needed</Text>
          <Text selectable style={{ lineHeight: 21, color: '#465268' }}>{analysis.nextEvidence}</Text>
        </View>
      </Card>

      <Card>
        <Text selectable style={{ fontSize: 18, fontWeight: '700' }}>Evidence Plus · Test Store</Text>
        {rcState.state === 'LOADING' ? <ActivityIndicator /> : null}
        <Text selectable style={{ color: '#4A5565' }}>RevenueCat state: {rcState.state}</Text>
        <Text selectable style={{ color: '#4A5565' }}>Entitlement: {rcState.isPremium ? 'ACTIVE' : 'INACTIVE'}</Text>
        {rcState.state === 'NOT_CONFIGURED' ? (
          <Text selectable style={{ color: '#7A5A00' }}>HOLD: add EXPO_PUBLIC_REVENUECAT_TEST_API_KEY at build/runtime. No key is stored in GitHub.</Text>
        ) : null}
        {rcState.error ? <Text selectable style={{ color: '#9B2C2C' }}>{rcState.error}</Text> : null}
        {rcState.isPremium ? (
          <View style={{ gap: 6, padding: 12, borderRadius: 12, backgroundColor: '#E8F5EE' }}>
            <Text selectable style={{ fontWeight: '800', color: '#176B45' }}>Deep checklist unlocked</Text>
            <Text selectable style={{ color: '#315A48' }}>Check source identity, baseline, comparison group, time window, measurement method, and independent replication.</Text>
          </View>
        ) : (
          <Pressable
            disabled={purchaseBusy || !rcState.packageToBuy}
            onPress={handlePurchase}
            style={({ pressed }) => ({ opacity: purchaseBusy || !rcState.packageToBuy ? 0.45 : 1, padding: 14, borderRadius: 14, backgroundColor: pressed ? '#26384F' : '#344B68', alignItems: 'center' })}
          >
            <Text selectable style={{ color: '#FFFFFF', fontWeight: '800' }}>{purchaseBusy ? 'Testing purchase…' : 'Unlock with Test Store'}</Text>
          </Pressable>
        )}
        {purchaseMessage ? <Text selectable style={{ color: '#344B68' }}>{purchaseMessage}</Text> : null}
      </Card>

      <Text selectable style={{ color: '#697586', lineHeight: 20, paddingBottom: 30 }}>
        Claim ceiling: educational evidence assessment only. This app is not a fact checker, scientific validator, or decision authority.
      </Text>
    </ScrollView>
  );
}
