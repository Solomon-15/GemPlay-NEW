import { useState, useEffect } from 'react';

const usePagination = (initialPage = 1, itemsPerPage = 10) => {
  const [currentPage, setCurrentPage] = useState(initialPage);
  const [totalPages, setTotalPages] = useState(1);
  const [totalItems, setTotalItems] = useState(0);

  const handlePageChange = (page) => {
    if (page >= 1 && page <= totalPages) {
      setCurrentPage(page);
    }
  };

  const updatePagination = (newTotalItems) => {
    const newTotalPages = Math.max(1, Math.ceil(newTotalItems / itemsPerPage));
    setTotalItems(newTotalItems);
    setTotalPages(newTotalPages);
    
    // Если текущая страница больше общего количества страниц, переходим на последнюю
    if (currentPage > newTotalPages) {
      setCurrentPage(newTotalPages);
    }
  };

  const resetPagination = () => {
    setCurrentPage(1);
    setTotalPages(1);
    setTotalItems(0);
  };

  const getPaginationParams = () => ({
    page: currentPage,
    limit: itemsPerPage,
    offset: (currentPage - 1) * itemsPerPage
  });

  // Сброс на первую страницу при изменении количества элементов на странице
  useEffect(() => {
    if (currentPage > totalPages && totalPages > 0) {
      setCurrentPage(1);
    }
  }, [itemsPerPage, totalPages, currentPage]);

  return {
    currentPage,
    totalPages,
    totalItems,
    itemsPerPage,
    handlePageChange,
    updatePagination,
    resetPagination,
    getPaginationParams,
    
    // Дополнительные вспомогательные методы
    isFirstPage: currentPage === 1,
    isLastPage: currentPage === totalPages,
    hasNextPage: currentPage < totalPages,
    hasPrevPage: currentPage > 1,
    startIndex: (currentPage - 1) * itemsPerPage,
    endIndex: Math.min(currentPage * itemsPerPage, totalItems)
  };
};

export default usePagination;