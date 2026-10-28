<script setup lang="ts">
import { computed, ref } from 'vue';
import type { ReviewCaseDetail } from '@casepilot/contracts';
import EvidenceLinks from './EvidenceLinks.vue';
import { formatDateTime, formatMoney, label } from '../domain/reviewCases';

const props = defineProps<{ detail: ReviewCaseDetail }>();
const materialType = ref('');
const materialObject = ref('');
const materialTypes = computed(() => [...new Set(props.detail.documents.map(item => item.materialType))]);
const materialObjects = computed(() => [...new Set(props.detail.documents.flatMap(item => [...item.claimIds, ...item.entityIds]))]);
const documents = computed(() => props.detail.documents.filter(item =>
  (!materialType.value || item.materialType === materialType.value)
  && (!materialObject.value || item.claimIds.includes(materialObject.value) || item.entityIds.includes(materialObject.value))));
function openDocument(url: string) { window.open(url, '_blank', 'noopener'); }
</script>

<template>
  <section class="review-case-detail">
    <section class="panel case-overview">
      <div><span class="label">当前案件</span><h2>{{ detail.id }} · 版本 {{ detail.revision }}</h2>
        <p>{{ detail.accident.accidentId }} · {{ formatDateTime(detail.accident.occurredAt) }} · {{ detail.accident.location }}</p>
        <small>演示数据 · 最近审查状态：{{ label(detail.latestReviewStatus) }} · 数据准备时间 {{ formatDateTime(detail.preparedAt) }}</small>
      </div>
      <div class="amount-summary">
        <span>原核赔金额<strong>{{ formatMoney(detail.originalApprovedAmount) }}</strong></span>
        <span>有效实付金额<strong>{{ formatMoney(detail.effectivePaidAmount) }}</strong></span>
      </div>
    </section>

    <section class="detail-grid two-columns">
      <article class="panel">
        <h2>事故与审查范围</h2>
        <dl class="fact-list"><dt>事故经过</dt><dd>{{ detail.accident.description }}</dd><dt>原责任记录</dt><dd>{{ detail.accident.liabilityDescription }}</dd><dt>损失范围</dt><dd>{{ detail.scope.lossTypes.map(label).join('、') }}</dd><dt>人伤原档案声明</dt><dd>{{ label(detail.injury.declaredStatus) }}</dd></dl>
        <div v-if="detail.scope.scopeLimitations.length" class="scope-limit"><strong>范围限制</strong><p v-for="item in detail.scope.scopeLimitations" :key="item">{{ item }}</p></div>
        <EvidenceLinks :case-id="detail.id" :sources="detail.accident.sources" />
      </article>
      <article class="panel">
        <h2>车辆与参与方</h2>
        <div v-for="vehicle in detail.vehicles" :key="vehicle.vehicleId" class="detail-card">
          <strong>{{ label(vehicle.role) }} · {{ vehicle.plateNumber }}</strong>
          <p>车主：{{ vehicle.ownerName ?? '未提供' }} · 驾驶人：{{ vehicle.driverName ?? '未提供' }}</p>
          <small>{{ vehicle.usage ?? '用途未提供' }} · {{ vehicle.powerType ?? '动力类型未提供' }}</small>
          <EvidenceLinks :case-id="detail.id" :sources="vehicle.sources" />
        </div>
      </article>
    </section>

    <section class="panel detail-section">
      <h2>赔案及原处理结果</h2>
      <div class="card-grid">
        <article v-for="claim in detail.claims" :key="claim.claimId" class="detail-card">
          <span class="tag">{{ label(claim.scopeRole) }}</span><strong>{{ claim.claimNumber }}</strong>
          <p>报案号：{{ claim.reportNumber }}</p>
          <dl class="fact-list compact"><dt>结案状态</dt><dd>{{ label(claim.closureType) }}</dd><dt>结案时间</dt><dd>{{ formatDateTime(claim.closedAt) }}</dd><dt>支付状态</dt><dd>{{ label(claim.originalPaymentStatus) }}</dd></dl>
          <p>{{ claim.originalConclusion }}</p>
          <EvidenceLinks :case-id="detail.id" :sources="claim.sources" />
        </article>
      </div>
    </section>

    <section class="panel detail-section">
      <h2>保单与承保险种</h2>
      <article v-for="policy in detail.policies" :key="policy.policyId" class="policy-card">
        <div><span class="tag">{{ label(policy.policyType) }}</span><strong>{{ policy.policyNumber ?? policy.policyId }}</strong><small>{{ label(policy.availability) }} · {{ formatDateTime(policy.effectiveFrom) }} 至 {{ formatDateTime(policy.effectiveTo) }}</small></div>
        <div class="card-grid">
          <div v-for="coverage in policy.coverages" :key="coverage.coverageId" class="detail-card">
            <strong>{{ label(coverage.coverageCode) }}</strong><small>{{ coverage.status === 'insured' ? '已承保' : label(coverage.status) }}</small>
            <dl class="fact-list compact"><dt>保险金额</dt><dd>{{ formatMoney(coverage.insuranceAmount) }}</dd><dt>每次事故限额</dt><dd>{{ formatMoney(coverage.perAccidentLimit) }}</dd><dt>免赔金额</dt><dd>{{ formatMoney(coverage.deductibleAmount) }}</dd></dl>
            <p v-if="coverage.specialConditions">{{ coverage.specialConditions }}</p>
            <small v-for="term in coverage.terms" :key="`${term.documentId}:${term.version}`">条款：{{ term.documentId }} / {{ term.version }} / {{ term.sectionIds.join('、') }}</small>
            <EvidenceLinks :case-id="detail.id" :sources="coverage.sources" />
          </div>
        </div>
        <EvidenceLinks :case-id="detail.id" :sources="policy.sources" />
      </article>
    </section>

    <section class="panel detail-section">
      <h2>损失与金额</h2>
      <div class="card-grid">
        <article v-for="loss in detail.losses" :key="loss.lossId" class="detail-card">
          <strong>{{ label(loss.lossType) }} · {{ loss.description }}</strong><small>关联赔案 {{ loss.claimId }}<template v-if="loss.vehicleId"> · 车辆 {{ loss.vehicleId }}</template></small>
          <dl class="fact-list compact"><dt>申请金额</dt><dd>{{ formatMoney(loss.claimedAmount) }}</dd><dt>定损金额</dt><dd>{{ formatMoney(loss.assessedAmount) }}</dd><dt>确认金额</dt><dd>{{ formatMoney(loss.agreedAmount) }}</dd></dl>
          <EvidenceLinks :case-id="detail.id" :sources="loss.sources" />
        </article>
      </div>
    </section>

    <section class="detail-grid two-columns">
      <article class="panel">
        <h2>原理算、核赔与支付</h2>
        <div v-for="record in detail.processingRecords" :key="record.recordId" class="detail-card">
          <strong>{{ record.title }} · {{ record.recordId }}</strong><small>{{ record.claimId }} · {{ label(record.status) }}<template v-if="record.occurredAt"> · {{ formatDateTime(record.occurredAt) }}</template></small>
          <p v-if="record.amount">{{ formatMoney(record.amount) }}</p><p v-if="record.detail">{{ record.detail }}</p>
          <EvidenceLinks :case-id="detail.id" :sources="record.sources" />
        </div>
      </article>
      <article class="panel">
        <h2>原作业时间线</h2>
        <div v-for="entry in detail.timeline" :key="entry.entryId" class="timeline-entry"><time>{{ formatDateTime(entry.occurredAt) }}</time><strong>{{ entry.title }}</strong><p>{{ entry.detail }}</p><EvidenceLinks :case-id="detail.id" :sources="entry.sources" /></div>
      </article>
    </section>

    <section v-if="detail.dataGaps.length || detail.scope.scopeLimitations.length" class="panel detail-section">
      <h2>资料缺口与范围限制</h2>
      <article v-for="gap in detail.dataGaps" :key="gap.gapId" class="gap-card"><strong>{{ gap.gapId }} · {{ label(gap.kind) }}</strong><p>{{ gap.description }}</p><small>影响对象：{{ gap.entityIds.join('、') }} · 字段：{{ gap.fieldPaths.join('、') }}</small><EvidenceLinks :case-id="detail.id" :sources="gap.sources" /></article>
      <div v-for="item in detail.scope.scopeLimitations" :key="item" class="scope-limit">{{ item }}</div>
    </section>

    <section class="panel detail-section">
      <h2>材料目录</h2>
      <div class="material-filters"><label>材料类别<select v-model="materialType"><option value="">全部</option><option v-for="item in materialTypes" :key="item" :value="item">{{ label(item) }}</option></select></label><label>关联对象<select v-model="materialObject"><option value="">全部</option><option v-for="item in materialObjects" :key="item" :value="item">{{ item }}</option></select></label></div>
      <div class="document-list">
        <article v-for="document in documents" :key="document.documentId" class="document-row">
          <div><strong>{{ document.title }}</strong><small>{{ label(document.materialType) }} · {{ label(document.status) }} · {{ document.version }}<template v-if="document.pageCount"> · {{ document.pageCount }} 页</template></small><p>{{ document.sourceDescription }}</p></div>
          <button v-if="document.contentUrl" type="button" class="secondary" @click="openDocument(document.contentUrl)">查看材料</button><span v-else class="muted">当前不可读取</span>
        </article>
        <p v-if="!documents.length" class="muted">没有符合当前材料筛选条件的记录。</p>
      </div>
    </section>
  </section>
</template>
