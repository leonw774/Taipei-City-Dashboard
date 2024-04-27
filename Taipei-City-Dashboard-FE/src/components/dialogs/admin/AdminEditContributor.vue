<!-- Developed by Taipei Urban Intelligence Center 2023-2024-->

<script setup>
import { defineProps } from "vue";
import { storeToRefs } from "pinia";
import { useDialogStore } from "../../../store/dialogStore";
import { useAdminStore } from "../../../store/adminStore";

import DialogContainer from "../DialogContainer.vue";

const dialogStore = useDialogStore();
const adminStore = useAdminStore();

const props = defineProps(["searchParams"]);

const { currentContributor } = storeToRefs(adminStore);

function handleConfirm() {
	adminStore.updateContributor(props.searchParams);
	handleClose();
}

function handleClose() {
	dialogStore.hideAllDialogs();
}
</script>

<template>
  <DialogContainer
    :dialog="`adminEditContributor`"
    @on-close="handleClose"
  >
    <div class="admineditcontributor">
      <div class="admineditcontributor-header">
        <h2>設定協作者</h2>
        <button @click="handleConfirm">
          確定更改
        </button>
      </div>
      <div class="admineditcontributor-settings">
        <div class="admineditcontributor-settings-items">
          <div class="two-block">
            <label>協作者名稱</label>
            <label>協作者 ID</label>
          </div>
          <div class="two-block">
            <input
              v-model="currentContributor.name"
              type="text"
              required
            >
            <input
              v-model="currentContributor.id"
              type="text"
              disabled
            >
          </div>
          <label>協作者個人連結</label>
          <input
            type="text"
            :value="currentContributor.link"
          >
          <label>協作者照片網址</label>
          <input
            type="text"
            :value="currentContributor.image"
          >
        </div>
      </div>
    </div>
  </DialogContainer>
</template>

<style scoped lang="scss">
.admineditcontributor {
	width: 350px;
	height: 400px;

	@media (max-width: 520px) {
		display: none;
	}
	@media (max-height: 520px) {
		display: none;
	}

	&-header {
		display: flex;
		justify-content: space-between;
		button {
			display: flex;
			align-items: center;
			justify-self: baseline;
			padding: 2px 4px;
			border-radius: 5px;
			background-color: var(--color-highlight);
			font-size: var(--font-ms);
		}
	}

	&-settings {
		height: calc(100% - 55px);
		padding: 0 0.5rem 0.5rem 0.5rem;
		margin-top: var(--font-ms);
		border-radius: 5px;
		border: solid 1px var(--color-border);
		overflow-y: scroll;

		label {
			margin: 8px 0 4px;
			font-size: var(--font-s);
			color: var(--color-complement-text);
		}

		.two-block {
			display: grid;
			grid-template-columns: 1fr 1fr;
			column-gap: 0.5rem;
		}
		.toggle {
			display: flex;
			flex-direction: row;
			align-items: center;
			column-gap: 6px;

			p {
				margin-top: 4px;
			}
		}

		&-items {
			display: flex;
			flex-direction: column;

			hr {
				margin: var(--font-ms) 0 0.5rem;
				border: none;
				border-bottom: dashed 1px var(--color-complement-text);
			}
		}

		&::-webkit-scrollbar {
			width: 4px;
		}
		&::-webkit-scrollbar-thumb {
			border-radius: 4px;
			background-color: rgba(136, 135, 135, 0.5);
		}
		&::-webkit-scrollbar-thumb:hover {
			background-color: rgba(136, 135, 135, 1);
		}
	}
}
</style>
