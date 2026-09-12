import React, { useEffect, useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  View,
} from 'react-native';
import { assessEvidence, AssessmentResult } from './src/assessment';
import { initializeRevenueCatPreview, RevenueCatState } from './src/revenuecat';

const initialRevenueCatState: RevenueCatState = {
  configured: false,
  offering: null,
  message: 'RevenueCat preview has not been checked yet.',
};

export default function App() {
  const [claim, setClaim] = useState('The school library is open after classes on Tuesday.');
  const [evidence, setEvidence] = useState('The school library is open after classes every Tuesday.');
  const [result, setResult] = useState<AssessmentResult | null>(null);
  const [revenueCat, setRevenueCat] = useState<RevenueCatState>(initialRevenueCatState);
  const [loadingRevenueCat, setLoadingRevenueCat] = useState(false);

  const packages = useMemo(
    () => revenueCat.offering?.availablePackages ?? [],
    [revenueCat.offering],
  );

  async function refreshRevenueCat() {
    setLoadingRevenueCat(true);
    try {
      setRevenueCat(await initializeRevenueCatPreview());
    } finally {
      setLoadingRevenueCat(false);
    }
  }

  useEffect(() => {
    void refreshRevenueCat();
  }, []);

  return (
    <ScrollView
      contentInsetAdjustmentBehavior="automatic"
      contentContainerStyle={{ padding: 20, gap: 18 }}
    >
      <View style={{ gap: 6 }}>
        <Text selectable style={{ fontSize: 30, fontWeight: '700' }}>
          ProofPath Mobile
        </Text>
        <Text selectable style={{ fontSize: 16, lineHeight: 22 }}>
          Learn what your evidence can actually support.
        </Text>
      </View>

      <View style={{ gap: 10 }}>
        <Text selectable style={{ fontWeight: '700', fontSize: 17 }}>Claim</Text>
        <TextInput
          multiline
          value={claim}
          onChangeText={setClaim}
          style={{ borderWidth: 1, borderColor: '#777', borderRadius: 14, padding: 14, minHeight: 92 }}
        />
        <Text selectable style={{ fontWeight: '700', fontSize: 17 }}>Evidence</Text>
        <TextInput
          multiline
          value={evidence}
          onChangeText={setEvidence}
          style={{ borderWidth: 1, borderColor: '#777', borderRadius: 14, padding: 14, minHeight: 110 }}
        />
        <Pressable
          onPress={() => setResult(assessEvidence(claim, evidence))}
          style={{ borderWidth: 1, borderRadius: 14, padding: 14, alignItems: 'center' }}
        >
          <Text selectable style={{ fontWeight: '700' }}>Assess evidence</Text>
        </Pressable>
      </View>

      {result ? (
        <View style={{ gap: 8, borderWidth: 1, borderRadius: 14, padding: 14 }}>
          <Text selectable style={{ fontSize: 20, fontWeight: '800' }}>{result.label}</Text>
          <Text selectable style={{ fontVariant: ['tabular-nums'] }}>
            Bounded score: {(result.confidence * 100).toFixed(0)}%
          </Text>
          <Text selectable style={{ lineHeight: 21 }}>{result.rationale}</Text>
          <Text selectable style={{ fontSize: 12, lineHeight: 17 }}>
            Educational demonstration only. This score is not calibrated scientific confidence and is not a universal truth verdict.
          </Text>
        </View>
      ) : null}

      <View style={{ gap: 10, borderWidth: 1, borderRadius: 14, padding: 14 }}>
        <Text selectable style={{ fontSize: 18, fontWeight: '800' }}>RevenueCat preview</Text>
        <Text selectable style={{ lineHeight: 20 }}>{revenueCat.message}</Text>
        <Text selectable style={{ fontSize: 12, lineHeight: 17 }}>
          Zero-spend demo mode: this build reads preview offering metadata only and contains no transaction action.
        </Text>
        {packages.map((pkg) => (
          <View key={pkg.identifier} style={{ gap: 2 }}>
            <Text selectable style={{ fontWeight: '700' }}>{pkg.identifier}</Text>
            <Text selectable>{pkg.product.title}</Text>
            <Text selectable>{pkg.product.priceString}</Text>
          </View>
        ))}
        <Pressable
          onPress={() => void refreshRevenueCat()}
          disabled={loadingRevenueCat}
          style={{ borderWidth: 1, borderRadius: 14, padding: 12, alignItems: 'center' }}
        >
          {loadingRevenueCat ? <ActivityIndicator /> : <Text selectable>Refresh preview offering</Text>}
        </Pressable>
      </View>
    </ScrollView>
  );
}
